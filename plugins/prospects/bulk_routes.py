"""Endpoints bulk prospects : enrichissement et suppression en masse."""
import json
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db

router = APIRouter()


class BulkIdsPayload(BaseModel):
    ids: List[str]


@router.post("/bulk-enrich")
async def bulk_enrich(
    payload: BulkIdsPayload,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Lance l'enrichissement waterfall sur une liste de prospects."""
    if not payload.ids:
        raise HTTPException(400, "Aucun ID fourni")
    if len(payload.ids) > 500:
        raise HTTPException(400, "Maximum 500 prospects à la fois")

    placeholders = ",".join(f":id{i}" for i in range(len(payload.ids)))
    params = {f"id{i}": v for i, v in enumerate(payload.ids)}

    count = (await db.execute(
        text(f"SELECT COUNT(*) FROM prospects WHERE id IN ({placeholders})"),
        params,
    )).scalar() or 0

    if count == 0:
        raise HTTPException(404, "Aucun prospect trouvé")

    background_tasks.add_task(_run_bulk_enrich, payload.ids)

    return {
        "message": f"Enrichissement lancé pour {count} prospect(s)",
        "queued": count,
    }


@router.post("/bulk-delete")
async def bulk_delete(
    payload: BulkIdsPayload,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Supprime une liste de prospects."""
    if not payload.ids:
        raise HTTPException(400, "Aucun ID fourni")

    placeholders = ",".join(f":id{i}" for i in range(len(payload.ids)))
    params = {f"id{i}": v for i, v in enumerate(payload.ids)}

    # Delete related records first
    try:
        await db.execute(
            text(f"DELETE FROM activities WHERE prospect_id IN ({placeholders})"),
            params,
        )
    except Exception as e:
        logger.warning(f"Delete activities failed: {e}")

    result = await db.execute(
        text(f"DELETE FROM prospects WHERE id IN ({placeholders})"),
        params,
    )
    await db.commit()

    deleted = result.rowcount if hasattr(result, "rowcount") else len(payload.ids)
    return {"message": f"{deleted} prospect(s) supprimé(s)", "deleted": deleted}


async def _run_bulk_enrich(ids: List[str]):
    """Background task — waterfall enrichment."""
    from core.database import AsyncSessionLocal

    try:
        from services.waterfall import WaterfallEnricher
    except ImportError:
        logger.warning("[bulk_enrich] WaterfallEnricher not available")
        return

    enricher = WaterfallEnricher()

    async with AsyncSessionLocal() as db:
        for pid in ids:
            try:
                row = (await db.execute(
                    text("SELECT id, company_name, siren, city, website FROM prospects WHERE id = :id"),
                    {"id": pid},
                )).fetchone()

                if not row:
                    continue

                prospect_data = {
                    "id": str(row[0]),
                    "company_name": row[1],
                    "siren": row[2],
                    "city": row[3],
                    "website": row[4],
                }

                enriched = await enricher.enrich(prospect_data)
                if not enriched:
                    continue

                update_fields = []
                params: dict = {"id": pid}
                for field in ("email", "phone", "website"):
                    if enriched.get(field):
                        update_fields.append(f"{field} = :{field}")
                        params[field] = enriched[field]

                if enriched.get("enrichment_data"):
                    update_fields.append("enrichment = CAST(:enrichment AS jsonb)")
                    params["enrichment"] = json.dumps(enriched["enrichment_data"])

                if update_fields:
                    await db.execute(
                        text(f"UPDATE prospects SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = :id"),
                        params,
                    )
                    await db.commit()

            except Exception as e:
                logger.warning(f"[bulk_enrich] failed for {pid}: {e}")
                continue
