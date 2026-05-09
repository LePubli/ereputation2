"""
Inbound Enrichment — Enrichit automatiquement les leads entrants.

Fonctionnement :
    1. Tu crées une "Source Inbound" → obtiens une URL webhook unique
    2. Typeform / HubSpot form / tout outil envoie les leads à cette URL
    3. Le système enrichit automatiquement via INSEE + scrapers
    4. Le prospect est créé dans B2B Prospector
    5. Optionnel : inscrit dans une séquence email automatiquement

Exemple URL : POST /api/v1/inbound/receive/tok_abc123xyz

Compatible avec :
    - Typeform (webhook natif)
    - HubSpot forms (webhook)
    - Tally.so
    - Google Forms (via Make/Zapier)
    - N'importe quelle app avec webhook sortant
"""
import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db

router = APIRouter(prefix="/api/v1/inbound", tags=["inbound"])


class InboundSourceCreate(BaseModel):
    name: str
    source_type: str = "webhook"  # webhook / typeform / hubspot
    field_mapping: dict = {}       # ex: {"email": "email", "company": "company_name", "siren": "siren"}
    auto_enrich: bool = True
    auto_sequence_id: UUID | None = None


class InboundSourceRead(BaseModel):
    id: str
    name: str
    token: str
    webhook_url: str
    source_type: str
    field_mapping: dict
    auto_enrich: bool
    is_active: bool
    leads_count: int
    created_at: str


@router.get("", response_model=list[InboundSourceRead])
async def list_sources(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.inbound_source import InboundSource
    result = await db.execute(select(InboundSource).order_by(InboundSource.created_at.desc()))
    sources = result.scalars().all()
    base_url = getattr(__import__('core.config', fromlist=['settings']), 'settings', None)
    return [
        InboundSourceRead(
            id=str(s.id),
            name=s.name,
            token=s.token,
            webhook_url=f"/api/v1/inbound/receive/{s.token}",
            source_type=s.source_type,
            field_mapping=s.field_mapping or {},
            auto_enrich=s.auto_enrich,
            is_active=s.is_active,
            leads_count=s.leads_count,
            created_at=s.created_at.isoformat(),
        )
        for s in sources
    ]


@router.post("", response_model=InboundSourceRead, status_code=status.HTTP_201_CREATED)
async def create_source(
    body: InboundSourceCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.inbound_source import InboundSource
    token = f"tok_{secrets.token_urlsafe(16)}"
    source = InboundSource(
        name=body.name,
        token=token,
        source_type=body.source_type,
        field_mapping=body.field_mapping,
        auto_enrich=body.auto_enrich,
        auto_sequence_id=body.auto_sequence_id,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return InboundSourceRead(
        id=str(source.id),
        name=source.name,
        token=source.token,
        webhook_url=f"/api/v1/inbound/receive/{source.token}",
        source_type=source.source_type,
        field_mapping=source.field_mapping or {},
        auto_enrich=source.auto_enrich,
        is_active=source.is_active,
        leads_count=source.leads_count,
        created_at=source.created_at.isoformat(),
    )


@router.post("/receive/{token}")
async def receive_lead(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint public — reçoit les leads de Typeform / HubSpot / etc.
    Pas d'authentification requise (token dans l'URL).
    """
    from models.database.inbound_source import InboundSource
    from models.database.prospect import Prospect
    from services.scrapers.aggregator import EnrichmentAggregator
    from services.scoring import score_prospect
    from services.queue import enqueue_siret_enrichment

    source = (await db.execute(
        select(InboundSource).where(
            InboundSource.token == token,
            InboundSource.is_active.is_(True),
        )
    )).scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source inbound introuvable ou inactive")

    # Parse le payload (JSON ou form)
    try:
        payload = await request.json()
    except Exception:
        payload = dict(await request.form())

    # Typage Typeform (les données sont dans payload.form_response.answers)
    if source.source_type == "typeform" and "form_response" in payload:
        payload = _parse_typeform(payload)

    # Mapping des champs selon la config
    mapping = source.field_mapping or {}
    mapped: dict = {}
    for our_field, their_field in mapping.items():
        val = payload.get(their_field) or payload.get(our_field)
        if val:
            mapped[our_field] = val

    # Champs par défaut
    company_name = mapped.get("company_name") or mapped.get("company") or payload.get("company")
    siren = mapped.get("siren") or payload.get("siren")
    email = mapped.get("email") or payload.get("email")

    if not company_name and not siren:
        return {"status": "skipped", "reason": "Aucun nom d'entreprise ni SIREN fourni"}

    # Créer le prospect
    prospect = Prospect(
        company_name=str(company_name or f"Lead inbound {datetime.now().strftime('%d/%m')}"),
        siren=str(siren)[:9] if siren else None,
        email=email,
        phone=mapped.get("phone") or payload.get("phone"),
        source="inbound",
        sources_used=["inbound"],
    )
    db.add(prospect)

    # Stage par défaut
    from sqlalchemy import select as sel
    from models.database.pipeline_stage import PipelineStage
    stage = (await db.execute(sel(PipelineStage).order_by(PipelineStage.order).limit(1))).scalar_one_or_none()
    if stage:
        prospect.stage_id = stage.id

    await db.flush()

    # Scoring initial
    await score_prospect(prospect)
    await db.commit()
    await db.refresh(prospect)

    # Enrichissement async (si SIREN dispo)
    if source.auto_enrich and siren:
        await enqueue_siret_enrichment(str(prospect.id), str(siren))

    # Inscription séquence auto
    if source.auto_sequence_id and email:
        from models.database.email_sequence import SequenceContact
        from datetime import timedelta
        sc = SequenceContact(
            sequence_id=source.auto_sequence_id,
            prospect_id=prospect.id,
            email=email,
            status="active",
            next_send_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        db.add(sc)

    # Incrémente le compteur
    source.leads_count = (source.leads_count or 0) + 1
    await db.commit()

    return {
        "status": "created",
        "prospect_id": str(prospect.id),
        "company_name": prospect.company_name,
        "enrichment_queued": bool(siren and source.auto_enrich),
    }


def _parse_typeform(payload: dict) -> dict:
    """Parse le format Typeform vers un dict plat."""
    result = {}
    answers = payload.get("form_response", {}).get("answers", [])
    for answer in answers:
        field_ref = answer.get("field", {}).get("ref", "")
        answer_type = answer.get("type", "")
        if answer_type == "text":
            result[field_ref] = answer.get("text", "")
        elif answer_type == "email":
            result[field_ref] = answer.get("email", "")
        elif answer_type == "phone_number":
            result[field_ref] = answer.get("phone_number", "")
        elif answer_type == "short_text":
            result[field_ref] = answer.get("text", "")
    return result
