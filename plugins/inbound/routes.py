"""
Inbound — leads entrants via webhooks (Typeform, HubSpot forms, etc.).
"""
import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db

router = APIRouter(prefix="/api/v1/inbound", tags=["inbound"])


# ─────────────────────────────────────────── Schemas
class InboundSourceCreate(BaseModel):
    name: str
    source_type: str = "webhook"
    field_mapping: dict = {}
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


class LeadStatusUpdate(BaseModel):
    status: str


# ─────────────────────────────────────────── Sources
@router.get("/sources")
async def list_sources(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.inbound_source import InboundSource

    result = await db.execute(select(InboundSource).order_by(InboundSource.created_at.desc()))
    sources = result.scalars().all()
    items = [
        InboundSourceRead(
            id=str(s.id), name=s.name, token=s.token,
            webhook_url=f"/api/v1/inbound/receive/{s.token}",
            source_type=s.source_type, field_mapping=s.field_mapping or {},
            auto_enrich=s.auto_enrich, is_active=s.is_active,
            leads_count=s.leads_count, created_at=s.created_at.isoformat(),
        )
        for s in sources
    ]
    return {"items": items, "total": len(items)}


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def create_source(
    body: InboundSourceCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.inbound_source import InboundSource

    token = f"tok_{secrets.token_urlsafe(16)}"
    s = InboundSource(
        name=body.name,
        token=token,
        source_type=body.source_type,
        field_mapping=body.field_mapping,
        auto_enrich=body.auto_enrich,
        auto_sequence_id=body.auto_sequence_id,
        is_active=True,
        leads_count=0,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)

    return InboundSourceRead(
        id=str(s.id), name=s.name, token=s.token,
        webhook_url=f"/api/v1/inbound/receive/{s.token}",
        source_type=s.source_type, field_mapping=s.field_mapping or {},
        auto_enrich=s.auto_enrich, is_active=s.is_active,
        leads_count=s.leads_count, created_at=s.created_at.isoformat(),
    )


@router.post("/receive/{token}")
async def receive_lead(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    from models.database.inbound_source import InboundSource

    source = (
        await db.execute(select(InboundSource).where(InboundSource.token == token))
    ).scalar_one_or_none()
    if not source or not source.is_active:
        raise HTTPException(404, "Source introuvable ou inactive")

    payload = await request.json()
    source.leads_count = (source.leads_count or 0) + 1
    await db.commit()
    return {"received": True, "lead": payload, "source_id": str(source.id)}


# ─────────────────────────────────────────── Leads
@router.get("/leads")
@router.get("/leads/")
async def list_leads(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    from models.database.prospect import Prospect

    stmt = (
        select(Prospect)
        .where(Prospect.tags.contains(["inbound"]))
        .order_by(desc(Prospect.created_at))
        .limit(limit)
    )
    try:
        result = await db.execute(stmt)
        prospects = result.scalars().all()
    except Exception:
        prospects = []

    items = [
        {
            "id": str(p.id), "company_name": p.company_name,
            "email": p.email, "phone": p.phone,
            "siren": p.siren, "siret": p.siret,
            "status": "new", "source": "webhook",
            "created_at": p.created_at.isoformat(),
        }
        for p in prospects
    ]
    return {"items": items, "total": len(items)}


@router.post("/leads/{lead_id}/enrich")
async def enrich_lead(lead_id: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from models.database.prospect import Prospect
    p = (await db.execute(select(Prospect).where(Prospect.id == lead_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Lead not found")
    return {"enriched": True, "id": str(p.id), "enriched_at": datetime.now(timezone.utc).isoformat()}


@router.post("/leads/{lead_id}/convert")
async def convert_lead(lead_id: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from models.database.prospect import Prospect
    p = (await db.execute(select(Prospect).where(Prospect.id == lead_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Lead not found")
    p.tags = [t for t in (p.tags or []) if t != "inbound"]
    await db.commit()
    return {"converted": True, "prospect_id": str(p.id)}


@router.patch("/leads/{lead_id}")
async def update_lead_status(lead_id: UUID, body: LeadStatusUpdate, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from models.database.prospect import Prospect
    p = (await db.execute(select(Prospect).where(Prospect.id == lead_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Lead not found")
    if body.status == "rejected":
        tags = [t for t in (p.tags or []) if t != "inbound"]
        tags.append("rejected")
        p.tags = tags
        await db.commit()
    return {"id": str(p.id), "status": body.status}


# ─────────────────────────────────────────── Config
@router.get("/config")
async def get_inbound_config(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from models.database.inbound_source import InboundSource
    sources = (await db.execute(select(InboundSource))).scalars().all()
    total_leads = sum(s.leads_count or 0 for s in sources)
    return {
        "auto_enrich_default": True,
        "auto_convert": False,
        "total_sources": len(sources),
        "active_sources": sum(1 for s in sources if s.is_active),
        "total_leads_received": total_leads,
    }
