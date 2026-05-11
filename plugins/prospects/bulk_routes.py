"""
Endpoints bulk pour les prospects : enrichissement et suppression en masse
À ajouter dans le plugin prospects/routes.py existant
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List
import logging

from core.database import get_db
from core.auth import get_current_active_user
from models.database.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


class BulkIdsPayload(BaseModel):
    ids: List[str]


@router.post("/bulk-enrich")
async def bulk_enrich(
    payload: BulkIdsPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lance l'enrichissement waterfall sur une liste de prospects"""
    if not payload.ids:
        raise HTTPException(400, "Aucun ID fourni")
    if len(payload.ids) > 500:
        raise HTTPException(400, "Maximum 500 prospects à la fois")

    # Verify prospects exist
    ids_str = "'" + "','".join(payload.ids) + "'"
    count = db.execute(text(
        f"SELECT COUNT(*) FROM prospects WHERE id IN ({ids_str})"
    )).scalar() or 0

    if count == 0:
        raise HTTPException(404, "Aucun prospect trouvé")

    # Schedule enrichment
    background_tasks.add_task(_run_bulk_enrich, payload.ids, db)

    return {
        "message": f"Enrichissement lancé pour {count} prospect(s)",
        "queued": count,
    }


@router.post("/bulk-delete")
async def bulk_delete(
    payload: BulkIdsPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Supprime une liste de prospects"""
    if not payload.ids:
        raise HTTPException(400, "Aucun ID fourni")

    ids_str = "'" + "','".join(payload.ids) + "'"

    # Delete related records first
    db.execute(text(f"DELETE FROM activities WHERE prospect_id IN ({ids_str})"))

    # Delete prospects
    result = db.execute(text(f"DELETE FROM prospects WHERE id IN ({ids_str})"))
    db.commit()

    deleted = result.rowcount if hasattr(result, 'rowcount') else len(payload.ids)
    return {"message": f"{deleted} prospect(s) supprimé(s)", "deleted": deleted}


async def _run_bulk_enrich(ids: List[str], db: Session):
    """Background task — waterfall enrichment"""
    try:
        from services.waterfall import WaterfallEnricher
        enricher = WaterfallEnricher()

        for pid in ids:
            try:
                row = db.execute(text(
                    "SELECT id, company_name, siren, city, website FROM prospects WHERE id = :id"
                ), {"id": pid}).fetchone()

                if not row:
                    continue

                prospect_data = {
                    "id": str(row[0]),
                    "company_name": row[1],
                    "siren": row[2],
                    "city": row[3],
                    "website": row[4],
                }

                # Run enrichment
                enriched = await enricher.enrich(prospect_data)

                if enriched:
                    # Update prospect with enriched data
                    update_fields = []
                    params = {"id": pid}

                    for field in ["email", "phone", "website", "linkedin_url", "employee_count"]:
                        if enriched.get(field):
                            update_fields.append(f"{field} = :{field}")
                            params[field] = enriched[field]

                    if enriched.get("enrichment_data"):
                        update_fields.append("enrichment_data = :enrichment_data::jsonb")
                        import json
                        params["enrichment_data"] = json.dumps(enriched["enrichment_data"])

                    if update_fields:
                        db.execute(text(
                            f"UPDATE prospects SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = :id"
                        ), params)
                        db.commit()

            except Exception as e:
                logger.warning(f"Enrichment failed for {pid}: {e}")
                continue

    except Exception as e:
        logger.error(f"Bulk enrich error: {e}")
