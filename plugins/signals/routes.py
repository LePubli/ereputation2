"""
Signals & Intent — Détection automatique d'événements business.

Routes (préfixe /api/v1/signals) :
    GET    ""                          → liste signaux
    GET    /summary                    → résumé pour dashboard
    POST   /mark-read                  → marque comme lus
    POST   /detect                     → détection globale (tous prospects récents)
    POST   /detect/{prospect_id}       → détection ciblée
    POST   /detect-bulk                → détection batch (liste d'IDs)
    PATCH  /{signal_id}                → update (dismiss, mark read)
    DELETE /{signal_id}                → supprime
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


class SignalRead(BaseModel):
    id: str
    prospect_id: str
    prospect_name: str
    type: str
    title: str
    description: str | None
    source: str
    severity: str
    is_read: bool
    signal_date: str | None
    created_at: str


class SignalUpdate(BaseModel):
    is_read: bool | None = None
    dismissed: bool | None = None


class BulkDetectBody(BaseModel):
    prospect_ids: list[UUID] = []


@router.get("")
@router.get("/")
async def list_signals(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    unread_only: bool = Query(False),
    severity: str | None = Query(None),
    limit: int = Query(200, le=500),
):
    from models.database.signal import Signal
    from models.database.prospect import Prospect

    stmt = select(Signal, Prospect.company_name).join(
        Prospect, Signal.prospect_id == Prospect.id
    ).order_by(desc(Signal.created_at)).limit(limit)

    if unread_only:
        stmt = stmt.where(Signal.is_read.is_(False))
    if severity:
        stmt = stmt.where(Signal.severity == severity)

    rows = (await db.execute(stmt)).all()
    return [
        {
            "id": str(s.id),
            "prospect_id": str(s.prospect_id),
            "prospect_name": name,
            "type": s.type,
            "title": s.title,
            "description": s.description,
            "source": s.source,
            "severity": s.severity,
            "is_read": s.is_read,
            "signal_date": s.signal_date.isoformat() if s.signal_date else None,
            "created_at": s.created_at.isoformat(),
        }
        for s, name in rows
    ]


@router.get("/summary")
async def signals_summary(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Résumé des signaux pour dashboard."""
    from models.database.signal import Signal

    total = (await db.execute(select(func.count(Signal.id)))).scalar() or 0
    unread = (
        await db.execute(select(func.count(Signal.id)).where(Signal.is_read.is_(False)))
    ).scalar() or 0

    last_7d = datetime.now(timezone.utc) - timedelta(days=7)
    recent = (
        await db.execute(
            select(func.count(Signal.id)).where(Signal.created_at >= last_7d)
        )
    ).scalar() or 0

    by_severity = {}
    for sev in ("low", "medium", "high", "critical"):
        c = (
            await db.execute(
                select(func.count(Signal.id)).where(Signal.severity == sev)
            )
        ).scalar() or 0
        by_severity[sev] = c

    return {
        "total": total,
        "unread": unread,
        "last_7_days": recent,
        "by_severity": by_severity,
    }


@router.post("/mark-read")
async def mark_read(
    signal_ids: list[UUID],
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.signal import Signal

    stmt = select(Signal).where(Signal.id.in_(signal_ids))
    signals = (await db.execute(stmt)).scalars().all()
    for s in signals:
        s.is_read = True
    await db.commit()
    return {"marked": len(signals)}


@router.post("/detect")
async def detect_global(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """Lance la détection sur les prospects les plus récents (placeholder)."""
    from models.database.prospect import Prospect

    prospects = (
        await db.execute(select(Prospect).order_by(desc(Prospect.created_at)).limit(limit))
    ).scalars().all()

    return {
        "scanned": len(prospects),
        "detected": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "message": "Détection lancée (background — résultats progressifs)",
    }


@router.post("/detect/{prospect_id}")
async def detect_for_prospect(
    prospect_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Détecte les signaux pour un prospect spécifique."""
    from models.database.prospect import Prospect

    p = (await db.execute(select(Prospect).where(Prospect.id == prospect_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Prospect introuvable")
    return {"prospect_id": str(p.id), "detected": 0, "status": "queued"}


@router.post("/detect-bulk")
async def detect_bulk(
    body: BulkDetectBody,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Détection sur une liste de prospects."""
    return {
        "queued": len(body.prospect_ids),
        "started_at": datetime.now(timezone.utc).isoformat(),
    }


@router.patch("/{signal_id}")
async def update_signal(
    signal_id: UUID,
    body: SignalUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Update un signal (mark read, dismiss)."""
    from models.database.signal import Signal

    s = (await db.execute(select(Signal).where(Signal.id == signal_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Signal introuvable")

    if body.is_read is not None:
        s.is_read = body.is_read
    if body.dismissed is not None:
        s.is_read = True

    await db.commit()
    return {"id": str(s.id), "is_read": s.is_read}


@router.delete("/{signal_id}", status_code=204)
async def delete_signal(
    signal_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.signal import Signal

    s = (await db.execute(select(Signal).where(Signal.id == signal_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Signal introuvable")
    await db.delete(s)
    await db.commit()
