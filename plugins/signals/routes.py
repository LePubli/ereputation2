"""
Signals & Intent — Détection automatique d'événements business.

Signaux détectés :
    bodacc_creation         — Entreprise créée récemment (< 6 mois)
    bodacc_procedure        — Procédure collective détectée (ALERTE)
    bodacc_capital_change   — Augmentation de capital (signal croissance)
    job_posting_detected    — Offres d'emploi actives (signal recrutement = croissance)
    news_mention            — Mention presse (via recherche web)
    website_change          — Nouveau site web (via AI Agent)
    inbound_form            — Lead entrant via formulaire

Usage Clay-style :
    - Chaque prospect a une liste de signaux détectés
    - Un signal peut déclencher une action (webhook, email, changement d'étape)
    - Dashboard "Signaux" : vue temps réel des événements récents
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
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


@router.get("", response_model=list[SignalRead])
async def list_signals(
    current_user: CurrentUser,
    unread_only: bool = Query(False),
    severity: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Liste les signaux récents (dashboard temps réel)."""
    from models.database.signal import Signal
    from models.database.prospect import Prospect
    from sqlalchemy import and_

    conditions = []
    if unread_only:
        conditions.append(Signal.is_read.is_(False))
    if severity:
        conditions.append(Signal.severity == severity)

    stmt = (
        select(Signal, Prospect.company_name)
        .join(Prospect, Signal.prospect_id == Prospect.id)
        .order_by(desc(Signal.created_at))
        .limit(limit)
    )
    if conditions:
        from sqlalchemy import and_
        stmt = stmt.where(and_(*conditions))

    rows = (await db.execute(stmt)).all()
    return [
        SignalRead(
            id=str(r.Signal.id),
            prospect_id=str(r.Signal.prospect_id),
            prospect_name=r.company_name,
            type=r.Signal.type,
            title=r.Signal.title,
            description=r.Signal.description,
            source=r.Signal.source,
            severity=r.Signal.severity,
            is_read=r.Signal.is_read,
            signal_date=r.Signal.signal_date.isoformat() if r.Signal.signal_date else None,
            created_at=r.Signal.created_at.isoformat(),
        )
        for r in rows
    ]


@router.post("/mark-read")
async def mark_read(
    signal_ids: list[UUID],
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Marque des signaux comme lus."""
    from models.database.signal import Signal
    from sqlalchemy import update
    await db.execute(
        update(Signal).where(Signal.id.in_(signal_ids)).values(is_read=True)
    )
    await db.commit()
    return {"marked": len(signal_ids)}


@router.post("/detect/{prospect_id}")
async def detect_signals_for_prospect(
    prospect_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Lance la détection de signaux pour UN prospect.
    Analyse : BODACC + AI web research.
    """
    from models.database.prospect import Prospect
    from models.database.signal import Signal

    prospect = (await db.execute(
        select(Prospect).where(Prospect.id == prospect_id)
    )).scalar_one_or_none()
    if not prospect:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prospect introuvable")

    detected = []

    # 1. Signaux BODACC depuis l'enrichissement existant
    bodacc = (prospect.enrichment or {}).get("bodacc_signals", {})
    if bodacc.get("has_collective_procedure"):
        sig = Signal(
            prospect_id=prospect_id,
            type="bodacc_procedure",
            title="⚠️ Procédure collective détectée",
            description=f"Annonces BODACC : {bodacc.get('annonces_count', 0)} publications.",
            source="bodacc",
            severity="critical",
            signal_date=datetime.now(timezone.utc),
        )
        db.add(sig)
        detected.append("bodacc_procedure")

    # 2. Entreprise récente (< 6 mois)
    if prospect.creation_date:
        from datetime import date
        try:
            creation = (
                prospect.creation_date
                if isinstance(prospect.creation_date, date)
                else date.fromisoformat(str(prospect.creation_date)[:10])
            )
            age_days = (date.today() - creation).days
            if age_days < 180:
                sig = Signal(
                    prospect_id=prospect_id,
                    type="bodacc_creation",
                    title="🆕 Entreprise créée récemment",
                    description=f"Créée il y a {age_days} jours — fenêtre d'opportunité idéale.",
                    source="insee",
                    severity="info",
                    signal_date=datetime.now(timezone.utc),
                )
                db.add(sig)
                detected.append("recent_company")
        except (ValueError, TypeError):
            pass

    # 3. Site web manquant (opportunité agence)
    if not prospect.website:
        sig = Signal(
            prospect_id=prospect_id,
            type="website_change",
            title="🌐 Aucun site web détecté",
            description="Opportunité pour une prestation web / référencement.",
            source="scraping",
            severity="info",
            signal_date=datetime.now(timezone.utc),
        )
        db.add(sig)
        detected.append("no_website")

    # 4. Score HOT sans contact récent
    if prospect.propensity_category == "HOT" and not prospect.last_activity_at:
        sig = Signal(
            prospect_id=prospect_id,
            type="hot_no_contact",
            title="🔥 Prospect HOT jamais contacté",
            description=f"Score {prospect.propensity_score:.0f}/100 — aucune activité enregistrée.",
            source="scoring",
            severity="warning",
            signal_date=datetime.now(timezone.utc),
        )
        db.add(sig)
        detected.append("hot_no_contact")

    await db.commit()
    return {"prospect_id": str(prospect_id), "detected": detected, "count": len(detected)}


@router.post("/detect-bulk")
async def detect_bulk(
    prospect_ids: list[UUID],
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Détection de signaux sur plusieurs prospects en masse."""
    import asyncio
    results = []
    for pid in prospect_ids[:100]:
        try:
            r = await detect_signals_for_prospect(pid, current_user, db)
            results.append(r)
        except Exception:
            pass
    return {"processed": len(results), "results": results}


@router.get("/summary")
async def signals_summary(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Résumé des signaux pour le dashboard."""
    from models.database.signal import Signal
    from sqlalchemy import func

    since = datetime.now(timezone.utc) - timedelta(days=7)

    total = (await db.execute(select(func.count(Signal.id)))).scalar_one()
    unread = (await db.execute(
        select(func.count(Signal.id)).where(Signal.is_read.is_(False))
    )).scalar_one()
    critical = (await db.execute(
        select(func.count(Signal.id)).where(Signal.severity == "critical", Signal.is_read.is_(False))
    )).scalar_one()
    recent = (await db.execute(
        select(func.count(Signal.id)).where(Signal.created_at >= since)
    )).scalar_one()

    return {
        "total": total,
        "unread": unread,
        "critical_unread": critical,
        "last_7_days": recent,
    }
