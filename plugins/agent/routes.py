"""Routes AI Agent — recherche IA par prospect ou en masse."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.config import settings
from core.database import get_db
from models.database.prospect import Prospect
from services.ai_agent import run_agent, bulk_agent_enrich

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


class AgentRequest(BaseModel):
    prospect_id: UUID
    prompt: str
    field: str | None = None        # champ à écrire dans ai_enrichment
    use_search: bool = True


class BulkAgentRequest(BaseModel):
    prospect_ids: list[UUID]
    prompt: str
    field: str
    use_search: bool = True


@router.post("/run")
async def run_agent_on_prospect(
    body: AgentRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Lance l'agent IA sur un prospect (Clay's Claygent equivalent)."""
    stmt = select(Prospect).where(Prospect.id == body.prospect_id)
    prospect = (await db.execute(stmt)).scalar_one_or_none()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect introuvable")

    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY non configurée. Ajouter dans les variables d'environnement Coolify.",
        )

    prospect_data = {
        "id": str(prospect.id),
        "company_name": prospect.company_name,
        "siren": prospect.siren,
        "siret": prospect.siret,
        "city": prospect.city,
        "postal_code": prospect.postal_code,
        "naf_code": prospect.naf_code,
        "naf_label": prospect.naf_label,
        "legal_form": prospect.legal_form,
        "employee_range": prospect.employee_range,
        "website": prospect.website,
        "phone": prospect.phone,
        "enrichment": prospect.enrichment or {},
    }

    result = await run_agent(
        prospect_data=prospect_data,
        prompt=body.prompt,
        use_search=body.use_search,
        anthropic_api_key=api_key,
    )

    # Écrire le résultat dans ai_enrichment si un champ est spécifié
    if body.field and result.get("result") is not None:
        ai_enrichment = dict(prospect.ai_enrichment or {})
        ai_enrichment[body.field] = {
            "value": result["result"],
            "source": result.get("source", "ai_agent"),
            "confidence": result.get("confidence", 0),
            "reasoning": result.get("reasoning", ""),
        }
        prospect.ai_enrichment = ai_enrichment
        await db.commit()

    return {
        "prospect_id": str(body.prospect_id),
        "prompt": body.prompt,
        "field": body.field,
        **result,
    }


@router.post("/bulk")
async def bulk_run(
    body: BulkAgentRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Lance l'agent sur plusieurs prospects en parallèle."""
    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY manquante")

    if len(body.prospect_ids) > 50:
        raise HTTPException(status_code=400, detail="Max 50 prospects en bulk")

    # Récupérer les prospects
    stmt = select(Prospect).where(Prospect.id.in_(body.prospect_ids))
    prospects = (await db.execute(stmt)).scalars().all()

    prospects_data = [
        {
            "id": str(p.id),
            "company_name": p.company_name,
            "siren": p.siren,
            "city": p.city,
            "naf_code": p.naf_code,
            "website": p.website,
            "enrichment": p.enrichment or {},
        }
        for p in prospects
    ]

    results = await bulk_agent_enrich(
        prospects=prospects_data,
        prompt=body.prompt,
        api_key=api_key,
        max_concurrent=3,
    )

    # Écrire les résultats en BDD
    updated = 0
    for r in results:
        if r.get("result") is not None:
            pid = r.get("prospect_id")
            p = next((x for x in prospects if str(x.id) == str(pid)), None)
            if p:
                ai_enrichment = dict(p.ai_enrichment or {})
                ai_enrichment[body.field] = {
                    "value": r["result"],
                    "confidence": r.get("confidence", 0),
                    "source": "ai_agent",
                }
                p.ai_enrichment = ai_enrichment
                updated += 1

    await db.commit()

    return {
        "processed": len(results),
        "updated": updated,
        "field": body.field,
        "results": results,
    }
