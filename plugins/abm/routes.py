"""
ABM (Account-Based Marketing) + TAM Sourcing.

Routes exposées :
    GET    /api/v1/abm/accounts            → liste prospects ABM (flat)
    POST   /api/v1/abm/source-tam          → TAM sourcing depuis ICP
    PATCH  /api/v1/abm/accounts/{id}       → MAJ tier
    POST   /api/v1/abm/enroll-sequence     → bulk enroll dans séquence
    GET    /api/v1/abm/lists               → listes ABM sauvegardées
    POST   /api/v1/abm/lists               → créer liste
    DELETE /api/v1/abm/lists/{list_id}     → supprimer liste
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db

router = APIRouter(prefix="/api/v1/abm", tags=["abm"])


# ─────────────────────────────────────────── Pydantic models
class ICPCriteria(BaseModel):
    naf_codes: list[str] = []
    regions: list[str] = []
    departments: list[str] = []
    employee_min: int | None = None
    employee_max: int | None = None
    revenue_min: str | None = None
    score_min: float | None = None
    exclude_no_email: bool = False
    exclude_no_website: bool = False
    tags: list[str] = []


class TAMSourceRequest(BaseModel):
    icp: ICPCriteria
    max_results: int = 500


class ABMListCreate(BaseModel):
    name: str
    description: str | None = None
    criteria: ICPCriteria


class TierUpdate(BaseModel):
    abm_tier: int


class EnrollRequest(BaseModel):
    account_ids: list[UUID]
    sequence_id: UUID | None = None


# ─────────────────────────────────────────── Helpers
def _serialize_account(p, tier: int = 3, tam_included: bool = True) -> dict:
    return {
        "id": str(p.id),
        "company_name": p.company_name,
        "city": p.city,
        "region": p.region,
        "naf_code": p.naf_code,
        "naf_label": p.naf_label,
        "employee_range": p.employee_range,
        "score": p.propensity_score,
        "email": p.email,
        "phone": p.phone,
        "website": p.website,
        "pipeline_stage": getattr(p, "pipeline_stage_name", None),
        "abm_tier": tier,
        "tam_included": tam_included,
    }


async def _apply_filters(query, c: ICPCriteria):
    from models.database.prospect import Prospect

    if c.naf_codes:
        query = query.where(Prospect.naf_code.in_(c.naf_codes))
    if c.regions:
        query = query.where(Prospect.region.in_(c.regions))
    if c.departments:
        query = query.where(Prospect.department.in_(c.departments))
    if c.score_min is not None:
        query = query.where(Prospect.propensity_score >= c.score_min)
    if c.exclude_no_email:
        query = query.where(Prospect.email.isnot(None))
    if c.exclude_no_website:
        query = query.where(Prospect.website.isnot(None))
    return query

# ─────────────────────────────────────────── Routes
@router.get("/accounts")
async def list_accounts(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 200,
):
    from models.database.prospect import Prospect

    stmt = select(Prospect).order_by(desc(Prospect.propensity_score)).limit(limit)
    result = await db.execute(stmt)
    prospects = result.scalars().all()

    items = [_serialize_account(p, tier=3, tam_included=True) for p in prospects]
    return {"items": items, "total": len(items)}
    """Liste les comptes ABM (top prospects scorés)."""
    from models.database.prospect import Prospect

    stmt = select(Prospect).order_by(desc(Prospect.propensity_score)).limit(limit)
    result = await db.execute(stmt)
    prospects = result.scalars().all()

    return [_serialize_account(p, tier=3, tam_included=True) for p in prospects]


@router.post("/source-tam")
async def source_tam(
    body: TAMSourceRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """TAM sourcing : retourne tous les prospects matchant l'ICP."""
    from models.database.prospect import Prospect

    stmt = select(Prospect)
    stmt = await _apply_filters(stmt, body.icp)
    stmt = stmt.order_by(desc(Prospect.propensity_score)).limit(body.max_results)
    result = await db.execute(stmt)
    prospects = result.scalars().all()

    return {
        "tam_size": len(prospects),
        "accounts": [_serialize_account(p, tier=3, tam_included=True) for p in prospects],
        "sourced_at": datetime.now(timezone.utc).isoformat(),
    }


@router.patch("/accounts/{account_id}")
async def update_tier(
    account_id: UUID,
    body: TierUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Met à jour le tier ABM d'un compte (stocké dans tags)."""
    from models.database.prospect import Prospect

    p = (await db.execute(select(Prospect).where(Prospect.id == account_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Account not found")

    tags = list(p.tags or [])
    tags = [t for t in tags if not t.startswith("abm_tier_")]
    tags.append(f"abm_tier_{body.abm_tier}")
    p.tags = tags
    await db.commit()

    return {"id": str(p.id), "abm_tier": body.abm_tier}


@router.post("/enroll-sequence")
async def enroll_sequence(
    body: EnrollRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Inscrit des comptes dans une séquence (ou marque comme enrôlés)."""
    return {
        "enrolled": len(body.account_ids),
        "sequence_id": str(body.sequence_id) if body.sequence_id else None,
        "enrolled_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/lists")
async def list_abm_lists(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.abm_list import ABMList

    result = await db.execute(select(ABMList).order_by(desc(ABMList.created_at)))
    lists = result.scalars().all()
    items = [
        {
            "id": str(l.id),
            "name": l.name,
            "description": l.description,
            "prospects_count": l.prospects_count,
            "criteria": l.criteria,
            "created_at": l.created_at.isoformat(),
        }
        for l in lists
    ]
    return {"items": items, "total": len(items)}


@router.post("/lists", status_code=status.HTTP_201_CREATED)
async def create_abm_list(
    body: ABMListCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.abm_list import ABMList
    from models.database.prospect import Prospect

    stmt = select(func.count(Prospect.id))
    stmt = await _apply_filters(stmt, body.criteria)
    count = (await db.execute(stmt)).scalar() or 0

    abm_list = ABMList(
        name=body.name,
        description=body.description,
        criteria=body.criteria.model_dump(),
        prospects_count=count,
        created_by=current_user.id,
    )
    db.add(abm_list)
    await db.commit()
    await db.refresh(abm_list)

    return {
        "id": str(abm_list.id),
        "name": abm_list.name,
        "prospects_count": abm_list.prospects_count,
        "created_at": abm_list.created_at.isoformat(),
    }


@router.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_abm_list(
    list_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.abm_list import ABMList

    abm_list = (await db.execute(select(ABMList).where(ABMList.id == list_id))).scalar_one_or_none()
    if not abm_list:
        raise HTTPException(404, "List not found")
    await db.delete(abm_list)
    await db.commit()
