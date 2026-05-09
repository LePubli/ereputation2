"""
ABM (Account-Based Marketing) + TAM Sourcing — Clay-style.

Fonctionnalités :
    - Créer des listes de comptes ciblés avec critères
    - TAM sourcing : trouver TOUS les prospects d'un segment (NAF + région)
    - Calcul du TAM (Total Addressable Market)
    - Scoring relatif dans la liste
    - Export vers séquence ou webhook

Exemple TAM sourcing :
    NAF: 62.01Z (dev logiciel) + Région: Hauts-de-France + 10-49 salariés
    → trouve toutes les entreprises correspondantes en BDD
    → complète avec l'INSEE si BDD insuffisante
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db

router = APIRouter(prefix="/api/v1/abm", tags=["abm"])


class ABMCriteria(BaseModel):
    naf_codes: list[str] = []
    regions: list[str] = []
    departments: list[str] = []
    employee_ranges: list[str] = []
    min_score: float | None = None
    has_website: bool | None = None
    tags: list[str] = []


class ABMListCreate(BaseModel):
    name: str
    description: str | None = None
    criteria: ABMCriteria


class TAMSourceRequest(BaseModel):
    criteria: ABMCriteria
    max_results: int = 500
    enrich_missing: bool = False


@router.get("")
async def list_abm_lists(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.abm_list import ABMList
    result = await db.execute(select(ABMList).order_by(desc(ABMList.created_at)))
    lists = result.scalars().all()
    return [
        {
            "id": str(l.id), "name": l.name, "description": l.description,
            "prospects_count": l.prospects_count, "criteria": l.criteria,
            "created_at": l.created_at.isoformat(),
        }
        for l in lists
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_abm_list(
    body: ABMListCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.abm_list import ABMList, ABMListProspect
    from models.database.prospect import Prospect

    # Build query depuis les critères
    prospects = await _query_by_criteria(body.criteria, db)

    abm = ABMList(
        name=body.name,
        description=body.description,
        criteria=body.criteria.model_dump(),
        prospects_count=len(prospects),
        created_by=current_user.id,
    )
    db.add(abm)
    await db.flush()

    for p in prospects:
        db.add(ABMListProspect(
            list_id=abm.id,
            prospect_id=p.id,
            score=p.propensity_score,
        ))

    await db.commit()
    await db.refresh(abm)
    return {
        "id": str(abm.id),
        "name": abm.name,
        "prospects_count": abm.prospects_count,
        "message": f"{abm.prospects_count} prospects correspondant aux critères",
    }


@router.post("/tam-source")
async def tam_source(
    body: TAMSourceRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    TAM Sourcing — Trouve toutes les entreprises correspondant aux critères.
    Retourne aussi les données INSEE manquantes pour compléter le TAM.
    """
    # Cherche dans la BDD existante
    prospects = await _query_by_criteria(body.criteria, db, limit=body.max_results)

    # Calcul TAM
    tam_data = {
        "in_database": len(prospects),
        "criteria": body.criteria.model_dump(),
        "segments": {},
        "top_prospects": [
            {
                "id": str(p.id),
                "company_name": p.company_name,
                "city": p.city,
                "naf_code": p.naf_code,
                "employee_range": p.employee_range,
                "propensity_score": p.propensity_score,
                "propensity_category": p.propensity_category,
                "website": p.website,
                "phone": p.phone,
            }
            for p in prospects[:50]
        ],
    }

    # Distribution par catégorie de score
    hot = sum(1 for p in prospects if p.propensity_category == "HOT")
    warm = sum(1 for p in prospects if p.propensity_category == "WARM")
    cold = sum(1 for p in prospects if p.propensity_category == "COLD")
    unscored = len(prospects) - hot - warm - cold

    tam_data["segments"] = {
        "HOT": hot,
        "WARM": warm,
        "COLD": cold,
        "unscored": unscored,
    }

    # Si peu de résultats en BDD, on peut sourcer depuis INSEE
    if body.enrich_missing and len(prospects) < 50 and body.criteria.naf_codes:
        insee_count = await _estimate_insee_tam(body.criteria)
        tam_data["insee_estimate"] = insee_count
        tam_data["coverage_rate"] = round((len(prospects) / max(insee_count, 1)) * 100, 1)

    return tam_data


@router.get("/{list_id}/prospects")
async def get_list_prospects(
    list_id: UUID,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 25,
    db: AsyncSession = Depends(get_db),
):
    from models.database.abm_list import ABMList, ABMListProspect
    from models.database.prospect import Prospect

    abm = (await db.execute(select(ABMList).where(ABMList.id == list_id))).scalar_one_or_none()
    if not abm:
        raise HTTPException(status_code=404, detail="Liste ABM introuvable")

    offset = (page - 1) * page_size
    stmt = (
        select(Prospect, ABMListProspect.score)
        .join(ABMListProspect, ABMListProspect.prospect_id == Prospect.id)
        .where(ABMListProspect.list_id == list_id)
        .order_by(desc(ABMListProspect.score))
        .offset(offset).limit(page_size)
    )
    rows = (await db.execute(stmt)).all()

    return {
        "list_name": abm.name,
        "total": abm.prospects_count,
        "page": page,
        "items": [
            {
                "id": str(r.Prospect.id),
                "company_name": r.Prospect.company_name,
                "city": r.Prospect.city,
                "naf_label": r.Prospect.naf_label,
                "employee_range": r.Prospect.employee_range,
                "propensity_score": r.Prospect.propensity_score,
                "propensity_category": r.Prospect.propensity_category,
                "website": r.Prospect.website,
                "phone": r.Prospect.phone,
                "email": r.Prospect.email,
                "abm_score": r.score,
            }
            for r in rows
        ],
    }


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(list_id: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from models.database.abm_list import ABMList
    abm = (await db.execute(select(ABMList).where(ABMList.id == list_id))).scalar_one_or_none()
    if not abm:
        raise HTTPException(status_code=404)
    await db.delete(abm)
    await db.commit()


# --- Helpers ---

async def _query_by_criteria(criteria: ABMCriteria, db, limit: int = 1000):
    from models.database.prospect import Prospect
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import cast

    conditions = []

    if criteria.naf_codes:
        conditions.append(Prospect.naf_code.in_(criteria.naf_codes))
    if criteria.regions:
        conditions.append(Prospect.region.in_(criteria.regions))
    if criteria.departments:
        conditions.append(Prospect.department.in_(criteria.departments))
    if criteria.employee_ranges:
        conditions.append(Prospect.employee_range.in_(criteria.employee_ranges))
    if criteria.min_score is not None:
        conditions.append(Prospect.propensity_score >= criteria.min_score)
    if criteria.has_website is True:
        conditions.append(Prospect.website.isnot(None))
    if criteria.has_website is False:
        conditions.append(Prospect.website.is_(None))
    if criteria.tags:
        for tag in criteria.tags:
            conditions.append(cast(Prospect.tags, JSONB).contains([tag]))

    stmt = select(Prospect).order_by(desc(Prospect.propensity_score)).limit(limit)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    return list((await db.execute(stmt)).scalars().all())


async def _estimate_insee_tam(criteria: ABMCriteria) -> int:
    """Estime le TAM depuis l'API INSEE pour les codes NAF donnés."""
    import httpx
    total = 0
    for naf in criteria.naf_codes[:3]:
        try:
            params = {"activite_principale": naf, "page": 1, "per_page": 1}
            if criteria.regions:
                params["region"] = criteria.regions[0][:2] if criteria.regions else None
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    "https://recherche-entreprises.api.gouv.fr/search",
                    params={k: v for k, v in params.items() if v},
                )
                if r.status_code == 200:
                    total += r.json().get("total_results", 0)
        except Exception:
            pass
    return total
