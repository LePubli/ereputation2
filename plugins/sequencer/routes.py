"""
Séquenceur Email — Phase 5 : SMTP réel + tracking opens/clics.
"""
import re
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.config import settings
from core.database import get_db

router = APIRouter(prefix="/api/v1/sequencer/sequences", tags=["sequencer"])


# ─────────────────────────────────────────── Schémas

class StepSchema(BaseModel):
    step_number: int
    wait_days: int = 0
    subject_template: str
    body_template: str
    use_ai_personalization: bool = False
    ai_personalization_prompt: str | None = None


class SequenceCreate(BaseModel):
    name: str
    description: str | None = None
    steps: list[StepSchema]


class EnrollRequest(BaseModel):
    prospect_ids: list[UUID]
    email_override: str | None = None


class SequenceStats(BaseModel):
    sequence_id: str
    name: str
    contacts_total: int
    contacts_active: int
    contacts_completed: int
    sent_total: int
    open_rate: float
    reply_rate: float


# ─────────────────────────────────────────── Helpers

def render_template(template: str, prospect: dict) -> str:
    def replace(match):
        key = match.group(1).strip()
        return str(prospect.get(key) or "")
    return re.sub(r'\{\{(\w+)\}\}', replace, template)


async def send_email_smtp(to_email: str, subject: str, body_html: str) -> bool:
    try:
        import aiosmtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        text_plain = re.sub(r'<[^>]+>', '', body_html)
        msg.attach(MIMEText(text_plain, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=False,
            start_tls=settings.SMTP_USE_TLS,
        )
        return True
    except Exception as e:
        from loguru import logger
        logger.error(f"[SMTP] Erreur envoi à {to_email}: {e}")
        return False


def build_html_email(body: str, tracking_id: str, base_url: str) -> str:
    """Wrap le body dans un template HTML avec pixel de tracking et lien désinscription."""
    pixel = f'<img src="{base_url}/api/v1/sequencer/track/open/{tracking_id}" width="1" height="1" style="display:none" />'
    unsubscribe = f'{base_url}/api/v1/sequencer/unsubscribe/{tracking_id}'

    # Convertit le texte brut en HTML basique si nécessaire
    if not body.strip().startswith("<"):
        body_html = body.replace("\n", "<br>")
    else:
        body_html = body

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:Arial,sans-serif;font-size:14px;line-height:1.6;color:#333;max-width:600px;margin:0 auto;padding:20px">
{body_html}
<br><br>
<hr style="border:none;border-top:1px solid #eee;margin:20px 0">
<p style="font-size:11px;color:#999">
  Vous recevez cet email car vous êtes dans notre base de données.
  <a href="{unsubscribe}" style="color:#999">Se désinscrire</a>
</p>
{pixel}
</body>
</html>"""


# ─────────────────────────────────────────── Routes

@router.get("")
@router.get("/")
async def list_sequences(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.email_sequence import EmailSequence, SequenceContact, SequenceStep
    result = await db.execute(
        select(EmailSequence).order_by(desc(EmailSequence.created_at))
    )
    seqs = result.scalars().all()

    items = []
    for s in seqs:
        # Compter contacts
        total = (await db.execute(
            select(func.count()).where(SequenceContact.sequence_id == s.id)
        )).scalar() or 0
        sent = (await db.execute(
            select(func.sum(SequenceContact.sent_count)).where(SequenceContact.sequence_id == s.id)
        )).scalar() or 0
        opens = (await db.execute(
            select(func.sum(SequenceContact.open_count)).where(SequenceContact.sequence_id == s.id)
        )).scalar() or 0
        replies = (await db.execute(
            select(func.sum(SequenceContact.reply_count)).where(SequenceContact.sequence_id == s.id)
        )).scalar() or 0
        steps_count = (await db.execute(
            select(func.count()).where(SequenceStep.sequence_id == s.id)
        )).scalar() or 0

        items.append({
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "is_active": s.is_active,
            "status": "active" if s.is_active else "paused",
            "enrolled_count": total,
            "sent_count": int(sent),
            "open_rate": round((int(opens) / int(sent)) * 100, 1) if sent else 0,
            "reply_rate": round((int(replies) / int(sent)) * 100, 1) if sent else 0,
            "steps": steps_count,
            "created_at": s.created_at.isoformat(),
        })
    return {"items": items, "total": len(items)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_sequence(
    body: SequenceCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.email_sequence import EmailSequence, SequenceStep
    seq = EmailSequence(
        name=body.name,
        description=body.description,
        created_by=current_user.id,
    )
    db.add(seq)
    await db.flush()

    for step_data in body.steps:
        step = SequenceStep(
            sequence_id=seq.id,
            step_number=step_data.step_number,
            wait_days=step_data.wait_days,
            subject_template=step_data.subject_template,
            body_template=step_data.body_template,
            use_ai_personalization=step_data.use_ai_personalization,
            ai_personalization_prompt=step_data.ai_personalization_prompt,
        )
        db.add(step)

    await db.commit()
    await db.refresh(seq)
    return {"id": str(seq.id), "name": seq.name, "steps_count": len(body.steps)}


@router.post("/{sequence_id}/enroll")
async def enroll_prospects(
    sequence_id: UUID,
    body: EnrollRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.email_sequence import EmailSequence, SequenceContact
    from models.database.prospect import Prospect

    seq = (await db.execute(
        select(EmailSequence).where(EmailSequence.id == sequence_id)
    )).scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Séquence introuvable")

    enrolled = 0
    skipped = 0

    for pid in body.prospect_ids:
        prospect = (await db.execute(
            select(Prospect).where(Prospect.id == pid)
        )).scalar_one_or_none()
        if not prospect:
            skipped += 1
            continue

        email = body.email_override or prospect.email
        if not email:
            skipped += 1
            continue

        existing = (await db.execute(
            select(SequenceContact).where(
                SequenceContact.sequence_id == sequence_id,
                SequenceContact.prospect_id == pid,
            )
        )).scalar_one_or_none()
        if existing:
            skipped += 1
            continue

        contact = SequenceContact(
            sequence_id=sequence_id,
            prospect_id=pid,
            email=email,
            current_step=0,
            status="active",
            next_send_at=datetime.now(timezone.utc) + timedelta(minutes=2),
        )
        db.add(contact)
        enrolled += 1

    await db.commit()

    # Lance le worker immédiatement pour le premier envoi
    if enrolled > 0:
        background_tasks.add_task(process_sequence_sends, str(sequence_id))

    return {"enrolled": enrolled, "skipped": skipped}


@router.get("/{sequence_id}/stats", response_model=SequenceStats)
async def get_stats(
    sequence_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.email_sequence import EmailSequence, SequenceContact

    seq = (await db.execute(
        select(EmailSequence).where(EmailSequence.id == sequence_id)
    )).scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404, detail="Séquence introuvable")

    contacts = (await db.execute(
        select(SequenceContact).where(SequenceContact.sequence_id == sequence_id)
    )).scalars().all()

    total = len(contacts)
    active = sum(1 for c in contacts if c.status == "active")
    completed = sum(1 for c in contacts if c.status == "completed")
    sent = sum(c.sent_count for c in contacts)
    opens = sum(c.open_count for c in contacts)
    replies = sum(c.reply_count for c in contacts)

    return SequenceStats(
        sequence_id=str(sequence_id),
        name=seq.name,
        contacts_total=total,
        contacts_active=active,
        contacts_completed=completed,
        sent_total=sent,
        open_rate=round((opens / sent) * 100, 1) if sent > 0 else 0,
        reply_rate=round((replies / sent) * 100, 1) if sent > 0 else 0,
    )


@router.post("/{sequence_id}/pause")
async def pause_sequence(
    sequence_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.email_sequence import EmailSequence
    seq = (await db.execute(
        select(EmailSequence).where(EmailSequence.id == sequence_id)
    )).scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404)
    seq.is_active = False
    await db.commit()
    return {"status": "paused"}


@router.post("/{sequence_id}/resume")
async def resume_sequence(
    sequence_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.email_sequence import EmailSequence
    seq = (await db.execute(
        select(EmailSequence).where(EmailSequence.id == sequence_id)
    )).scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404)
    seq.is_active = True
    await db.commit()
    return {"status": "active"}


@router.delete("/{sequence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sequence(
    sequence_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.email_sequence import EmailSequence
    seq = (await db.execute(
        select(EmailSequence).where(EmailSequence.id == sequence_id)
    )).scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404)
    await db.delete(seq)
    await db.commit()


# ─────────────────────────────────────────── Tracking (public, sans auth)

@router.get("/track/open/{tracking_id}", include_in_schema=False)
async def track_open(tracking_id: str, db: AsyncSession = Depends(get_db)):
    """Pixel de tracking d'ouverture."""
    from models.database.email_sequence import EmailSend, SequenceContact
    try:
        send = (await db.execute(
            select(EmailSend).where(EmailSend.tracking_id == tracking_id)
        )).scalar_one_or_none()
        if send and not send.opened_at:
            send.opened_at = datetime.now(timezone.utc)
            send.status = "opened"
            # Incrémente open_count du contact
            contact = (await db.execute(
                select(SequenceContact).where(SequenceContact.id == send.sequence_contact_id)
            )).scalar_one_or_none()
            if contact:
                contact.open_count = (contact.open_count or 0) + 1
            await db.commit()
    except Exception:
        pass
    # Retourne GIF 1x1 transparent
    gif = b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
    return Response(content=gif, media_type="image/gif")


@router.get("/unsubscribe/{tracking_id}", include_in_schema=False)
async def unsubscribe(tracking_id: str, db: AsyncSession = Depends(get_db)):
    """Désinscription via lien dans l'email."""
    from models.database.email_sequence import EmailSend, SequenceContact
    try:
        send = (await db.execute(
            select(EmailSend).where(EmailSend.tracking_id == tracking_id)
        )).scalar_one_or_none()
        if send:
            contact = (await db.execute(
                select(SequenceContact).where(SequenceContact.id == send.sequence_contact_id)
            )).scalar_one_or_none()
            if contact:
                contact.unsubscribed = True
                contact.status = "unsubscribed"
                await db.commit()
    except Exception:
        pass
    return Response(
        content="<html><body style='font-family:sans-serif;text-align:center;padding:40px'><h2>✅ Désinscription enregistrée</h2><p>Vous ne recevrez plus d'emails de notre part.</p></body></html>",
        media_type="text/html",
    )


# ─────────────────────────────────────────── Worker d'envoi

async def process_sequence_sends(sequence_id: str | None = None):
    """
    Worker d'envoi — à appeler via BackgroundTasks ou ARQ cron.
    Traite les contacts dont next_send_at <= now.
    """
    from sqlalchemy import and_
    from models.database.email_sequence import (
        EmailSequence, SequenceContact, SequenceStep, EmailSend
    )
    from models.database.prospect import Prospect
    from core.database import AsyncSessionLocal
    from loguru import logger

    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
    sent_count = 0
    error_count = 0

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)

        # Filtre par séquence si fourni
        where_clauses = [
            SequenceContact.status == "active",
            SequenceContact.next_send_at <= now,
            SequenceContact.unsubscribed.is_(False),
            SequenceContact.bounced.is_(False),
        ]
        if sequence_id:
            where_clauses.append(SequenceContact.sequence_id == UUID(sequence_id))

        stmt = select(SequenceContact).where(and_(*where_clauses)).limit(100)
        contacts = (await db.execute(stmt)).scalars().all()

        for contact in contacts:
            try:
                seq = (await db.execute(
                    select(EmailSequence).where(EmailSequence.id == contact.sequence_id)
                )).scalar_one_or_none()
                if not seq or not seq.is_active:
                    contact.status = "paused"
                    continue

                step = (await db.execute(
                    select(SequenceStep).where(
                        SequenceStep.sequence_id == contact.sequence_id,
                        SequenceStep.step_number == contact.current_step + 1,
                    )
                )).scalar_one_or_none()

                if not step:
                    contact.status = "completed"
                    contact.next_send_at = None
                    continue

                prospect = (await db.execute(
                    select(Prospect).where(Prospect.id == contact.prospect_id)
                )).scalar_one_or_none()
                if not prospect:
                    contact.status = "error"
                    continue

                prospect_dict = {
                    "company_name": prospect.company_name or "",
                    "first_name": "",
                    "last_name": "",
                    "city": prospect.city or "",
                    "naf_label": prospect.naf_label or "",
                    "website": prospect.website or "",
                    "phone": prospect.phone or "",
                    "siren": prospect.siren or "",
                    "email": contact.email,
                }

                subject = render_template(step.subject_template, prospect_dict)
                body = render_template(step.body_template, prospect_dict)

                # Personnalisation IA optionnelle
                if step.use_ai_personalization and step.ai_personalization_prompt and api_key:
                    try:
                        from services.ai_agent import run_agent
                        result = await run_agent(
                            prospect_data=prospect_dict,
                            prompt=f"{step.ai_personalization_prompt}\n\nTemplate:\n{body}\n\nRetourne UNIQUEMENT le corps personnalisé.",
                            use_search=False,
                            anthropic_api_key=api_key,
                        )
                        body = result.get("result") or result.get("raw_response") or body
                    except Exception as ai_err:
                        logger.warning(f"[Sequencer] AI personalization failed: {ai_err}")

                # Génère tracking_id et construit l'email
                tracking_id = secrets.token_urlsafe(16)
                body_html = build_html_email(body, tracking_id, base_url)

                success = await send_email_smtp(contact.email, subject, body_html)

                # Enregistre l'envoi
                email_send = EmailSend(
                    sequence_contact_id=contact.id,
                    step_number=step.step_number,
                    subject=subject,
                    body_html=body_html,
                    sent_at=now if success else None,
                    status="sent" if success else "failed",
                    error=None if success else "SMTP failed",
                )
                # Ajoute tracking_id si le modèle le supporte
                if hasattr(email_send, "tracking_id"):
                    email_send.tracking_id = tracking_id

                db.add(email_send)

                if success:
                    contact.sent_count = (contact.sent_count or 0) + 1
                    contact.last_sent_at = now
                    contact.current_step = step.step_number
                    sent_count += 1
                else:
                    error_count += 1

                # Planifie l'étape suivante
                next_step = (await db.execute(
                    select(SequenceStep).where(
                        SequenceStep.sequence_id == contact.sequence_id,
                        SequenceStep.step_number == step.step_number + 1,
                    )
                )).scalar_one_or_none()

                if next_step:
                    contact.next_send_at = now + timedelta(days=next_step.wait_days or 1)
                else:
                    contact.status = "completed"
                    contact.next_send_at = None

            except Exception as e:
                logger.exception(f"[Sequencer] Erreur contact {contact.id}: {e}")
                error_count += 1
                continue

        await db.commit()
        logger.info(f"[Sequencer] Traité {len(contacts)} contacts : {sent_count} envoyés, {error_count} erreurs")

    return {"sent": sent_count, "errors": error_count, "processed": len(contacts) if 'contacts' in dir() else 0}


# ARQ task wrapper
async def task_process_sequences(ctx: dict) -> dict:
    return await process_sequence_sends()
