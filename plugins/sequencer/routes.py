"""
Séquenceur Email Clay-style.

Fonctionnalités :
- Séquences multi-étapes avec délai entre chaque email
- Templates avec variables {{company_name}}, {{city}}, {{first_name}}...
- Personnalisation IA (Claude génère le contenu par prospect)
- Suivi : envois, ouvertures, réponses, désabonnements
- Worker ARQ pour envois automatisés

Exemple de séquence :
    Étape 1 (J+0) : Email de prise de contact
    Étape 2 (J+3) : Relance courte si pas de réponse
    Étape 3 (J+7) : Email de valeur (cas client)
    Étape 4 (J+14) : Break-up email
"""
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.config import settings
from core.database import get_db

router = APIRouter(prefix="/api/v1/sequencer/sequences", tags=["sequencer"])

# --- Schémas ---

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
    email_override: str | None = None  # si pas d'email sur le prospect


class SequenceStats(BaseModel):
    sequence_id: str
    name: str
    contacts_total: int
    contacts_active: int
    contacts_completed: int
    sent_total: int
    open_rate: float
    reply_rate: float


# --- Helpers ---

def render_template(template: str, prospect: dict) -> str:
    """Remplace les variables {{field}} par les vraies valeurs."""
    def replace(match):
        key = match.group(1).strip()
        return str(prospect.get(key) or "")
    return re.sub(r'\{\{(\w+)\}\}', replace, template)


async def personalize_with_ai(
    body: str,
    prospect: dict,
    prompt: str,
    api_key: str,
) -> str:
    """Utilise Claude pour personnaliser un email."""
    from services.ai_agent import run_agent
    result = await run_agent(
        prospect_data=prospect,
        prompt=f"{prompt}\n\nVoici le template de base:\n{body}\n\nRetourne UNIQUEMENT le corps de l'email personnalisé, sans JSON, sans markup.",
        use_search=False,
        anthropic_api_key=api_key,
    )
    raw = result.get("result") or result.get("raw_response") or body
    return str(raw)


async def send_email_smtp(
    to_email: str,
    subject: str,
    body_html: str,
) -> bool:
    """Envoie un email via SMTP PlanetHoster."""
    try:
        import aiosmtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        # Version HTML
        html_part = MIMEText(body_html, "html", "utf-8")
        # Version texte (strip des balises)
        text_plain = re.sub(r'<[^>]+>', '', body_html)
        text_part = MIMEText(text_plain, "plain", "utf-8")
        msg.attach(text_part)
        msg.attach(html_part)

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


# --- Endpoints ---

@router.get("")
async def list_sequences(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.email_sequence import EmailSequence
    result = await db.execute(
        select(EmailSequence).order_by(desc(EmailSequence.created_at))
    )
    seqs = result.scalars().all()
    return [{"id": str(s.id), "name": s.name, "description": s.description, "is_active": s.is_active,
             "created_at": s.created_at.isoformat()} for s in seqs]


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
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Inscrit des prospects à une séquence et planifie le premier envoi."""
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

        # Vérif doublon
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
            next_send_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db.add(contact)
        enrolled += 1

    await db.commit()
    return {"enrolled": enrolled, "skipped": skipped}


@router.get("/{sequence_id}/stats", response_model=SequenceStats)
async def get_stats(
    sequence_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func
    from models.database.email_sequence import EmailSequence, SequenceContact, EmailSend

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
async def pause_sequence(sequence_id: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from models.database.email_sequence import EmailSequence
    seq = (await db.execute(select(EmailSequence).where(EmailSequence.id == sequence_id))).scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404)
    seq.is_active = False
    await db.commit()
    return {"status": "paused"}


@router.delete("/{sequence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sequence(sequence_id: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from models.database.email_sequence import EmailSequence
    seq = (await db.execute(select(EmailSequence).where(EmailSequence.id == sequence_id))).scalar_one_or_none()
    if not seq:
        raise HTTPException(status_code=404)
    await db.delete(seq)
    await db.commit()


# --- Worker ARQ (tâche planifiée) ---

async def task_process_sequences(ctx: dict) -> dict:
    """
    Tâche ARQ — envoie les emails planifiés de toutes les séquences actives.
    À lancer toutes les 5 minutes via cron ARQ.
    """
    from sqlalchemy import and_
    from models.database.email_sequence import (
        EmailSequence, SequenceContact, SequenceStep, EmailSend
    )
    from models.database.prospect import Prospect
    from core.database import AsyncSessionLocal
    from loguru import logger

    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    sent_count = 0
    error_count = 0

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)

        # Récupère tous les contacts à envoyer maintenant
        stmt = select(SequenceContact).where(
            and_(
                SequenceContact.status == "active",
                SequenceContact.next_send_at <= now,
                SequenceContact.unsubscribed.is_(False),
                SequenceContact.bounced.is_(False),
            )
        ).limit(50)  # max 50 par batch

        contacts = (await db.execute(stmt)).scalars().all()

        for contact in contacts:
            try:
                # Charge la séquence et l'étape courante
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
                    continue

                # Charge le prospect
                prospect = (await db.execute(
                    select(Prospect).where(Prospect.id == contact.prospect_id)
                )).scalar_one_or_none()
                if not prospect:
                    contact.status = "error"
                    continue

                prospect_dict = {
                    "company_name": prospect.company_name,
                    "first_name": (prospect.contacts[0].first_name if prospect.contacts else ""),
                    "last_name": (prospect.contacts[0].last_name if prospect.contacts else ""),
                    "city": prospect.city,
                    "naf_label": prospect.naf_label,
                    "website": prospect.website,
                    "phone": prospect.phone,
                    "siren": prospect.siren,
                }

                # Rendu du template
                subject = render_template(step.subject_template, prospect_dict)
                body = render_template(step.body_template, prospect_dict)

                # Personnalisation IA si activée
                if step.use_ai_personalization and step.ai_personalization_prompt and api_key:
                    body = await personalize_with_ai(body, prospect_dict, step.ai_personalization_prompt, api_key)

                # Ajout pixel de tracking (optionnel)
                tracking_id = secrets.token_urlsafe(16)
                body_html = f"{body}<img src='/api/v1/sequences/track/open/{tracking_id}' width='1' height='1' style='display:none'/>"

                # Envoi SMTP
                success = await send_email_smtp(contact.email, subject, body_html)

                # Enregistrement
                email_send = EmailSend(
                    sequence_contact_id=contact.id,
                    step_number=step.step_number,
                    subject=subject,
                    body_html=body_html,
                    sent_at=now if success else None,
                    status="sent" if success else "failed",
                    error=None if success else "SMTP failed",
                )
                db.add(email_send)

                if success:
                    contact.sent_count += 1
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
                    contact.next_send_at = now + timedelta(days=next_step.wait_days)
                else:
                    contact.status = "completed"
                    contact.next_send_at = None

            except Exception as e:
                logger.exception(f"[Sequencer] Erreur contact {contact.id}: {e}")
                error_count += 1

        await db.commit()

    return {"sent": sent_count, "errors": error_count, "processed": len(contacts)}


@router.get("/track/open/{tracking_id}")
async def track_open(tracking_id: str):
    """Pixel de tracking d'ouverture (1x1 GIF transparent)."""
    from fastapi.responses import Response
    # GIF 1x1 transparent
    gif = b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"
    return Response(content=gif, media_type="image/gif")
