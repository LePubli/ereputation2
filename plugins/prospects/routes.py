"""Routes prospects Phase 2 — filtres avancés, export CSV, SSE, auth."""
import asyncio
import csv
import io
import json
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser, OptionalUser
from core.database import get_db
from models.schemas.prospect import (
    ProspectCreate,
    ProspectCreateBySiret,
    ProspectImportResult,
    ProspectListResponse,
    ProspectRead,
    ProspectStageUpdate,
    ProspectUpdate,
)
from plugins.prospects.service import ProspectService
from .bulk_routes import router as bulk_router
router = APIRouter(prefix="/api/v1/prospects", tags=["prospects"])


# =============================================================================
# LIST — filtres avancés
# =============================================================================

@router.get("", response_model=ProspectListResponse)
@router.get("/", response_model=ProspectListResponse, include_in_schema=False)
async def list_prospects(    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = Query(None),
    stage_id: UUID | None = Query(None),
    naf_code: str | None = Query(None),
    region: str | None = Query(None),
    department: str | None = Query(None, max_length=3),
    propensity_category: str | None = Query(None, pattern="^(HOT|WARM|COLD)$"),
    source: str | None = Query(None),
    has_website: bool | None = Query(None),
    has_phone: bool | None = Query(None),
    min_score: float | None = Query(None, ge=0, le=100),
    tags: str | None = Query(None),
    sort_by: str = Query("created_at", pattern="^(created_at|company_name|propensity_score|estimated_revenue|last_activity_at|score)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    service = ProspectService(db)
    tags_list = [t.strip() for t in tags.split(",")] if tags else None

    if sort_by == "score":
        sort_by = "propensity_score"

    items, total = await service.list_prospects(
        page=page, page_size=page_size, search=search, stage_id=stage_id,
        naf_code=naf_code, region=region, department=department,
        propensity_category=propensity_category, source=source,
        has_website=has_website, has_phone=has_phone,
        min_score=min_score, tags=tags_list,
        sort_by=sort_by, sort_dir=sort_dir,
    )
    return ProspectListResponse(
        items=[ProspectRead.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
    )


# =============================================================================
# EXPORT CSV
# =============================================================================

@router.get("/export/csv")
async def export_csv(
    current_user: CurrentUser,
    search: str | None = Query(None),
    stage_id: UUID | None = Query(None),
    naf_code: str | None = Query(None),
    region: str | None = Query(None),
    propensity_category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = ProspectService(db)
    items, _ = await service.list_prospects(
        page=1, page_size=10000,
        search=search, stage_id=stage_id,
        naf_code=naf_code, region=region,
        propensity_category=propensity_category,
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "company_name", "siren", "siret", "naf_code", "naf_label",
        "legal_form", "employee_range", "creation_date",
        "address", "postal_code", "city", "department", "region",
        "phone", "email", "website",
        "propensity_score", "propensity_category", "estimated_revenue",
        "sources_used", "tags", "created_at",
    ])
    for p in items:
        writer.writerow([
            p.company_name, p.siren or "", p.siret or "",
            p.naf_code or "", p.naf_label or "",
            p.legal_form or "", p.employee_range or "",
            p.creation_date or "",
            p.address or "", p.postal_code or "", p.city or "",
            p.department or "", p.region or "",
            p.phone or "", p.email or "", p.website or "",
            p.propensity_score or "", p.propensity_category or "",
            p.estimated_revenue or "",
            ",".join(p.sources_used),
            ",".join(p.tags),
            p.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=prospects.csv"},
    )


# =============================================================================
# SSE — Server-Sent Events
# =============================================================================

@router.get("/events/{prospect_id}")
async def sse_prospect_events(prospect_id: str, current_user: CurrentUser):
    import redis.asyncio as aioredis
    from core.config import settings

    async def event_generator():
        try:
            r = aioredis.from_url(settings.REDIS_URL)
            pubsub = r.pubsub()
            await pubsub.subscribe(f"prospect:{prospect_id}")
            yield f"data: {json.dumps({'event': 'connected', 'prospect_id': prospect_id})}\n\n"
            timeout, elapsed = 120, 0
            while elapsed < timeout:
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg.get("data"):
                    yield f"data: {msg['data'].decode()}\n\n"
                    break
                await asyncio.sleep(1)
                elapsed += 1
                if elapsed % 15 == 0:
                    yield f"data: {json.dumps({'event': 'heartbeat'})}\n\n"
            await pubsub.unsubscribe(f"prospect:{prospect_id}")
            await r.close()
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# =============================================================================
# Routes statiques AVANT /{prospect_id}
# =============================================================================

@router.get("/contacts/providers")
async def list_contact_providers(current_user: CurrentUser):
    return {
        "providers": [
            {"id": "smtp_verify", "name": "SMTP Verify", "available": True},
            {"id": "hunter", "name": "Hunter.io", "available": False},
            {"id": "dropcontact", "name": "Dropcontact", "available": False},
        ]
    }


# =============================================================================
# CRUD standard
# =============================================================================

@router.post("", response_model=ProspectRead, status_code=status.HTTP_201_CREATED)
async def create_manual(data: ProspectCreate, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    service = ProspectService(db)
    from services.scoring import score_prospect
    prospect = await service.create_manual(data)
    await score_prospect(prospect)
    await db.commit()
    await db.refresh(prospect)
    return ProspectRead.model_validate(prospect)


@router.post("/by-siret", response_model=ProspectRead, status_code=status.HTTP_201_CREATED)
async def create_by_siret(data: ProspectCreateBySiret, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from services.queue import enqueue_siret_enrichment
    from services.scoring import score_prospect

    service = ProspectService(db)
    try:
        prospect = await service.create_by_identifier(data.identifier, fast_only=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Enrichissement impossible : {str(e)[:200]}")

    await score_prospect(prospect)
    await db.commit()
    await db.refresh(prospect)
    await enqueue_siret_enrichment(str(prospect.id), data.identifier)
    return ProspectRead.model_validate(prospect)


@router.post("/import", response_model=ProspectImportResult)
async def import_file(current_user: CurrentUser, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Fichier sans nom")
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fichier > 10 MB")
    service = ProspectService(db)
    return await service.import_from_file(contents, file.filename)


@router.get("/{prospect_id}", response_model=ProspectRead)
async def get_prospect(prospect_id: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    service = ProspectService(db)
    p = await service.get_prospect(prospect_id)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    return ProspectRead.model_validate(p)


@router.patch("/{prospect_id}", response_model=ProspectRead)
async def update_prospect(prospect_id: UUID, data: ProspectUpdate, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from services.scoring import score_prospect
    service = ProspectService(db)
    p = await service.update(prospect_id, data)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    await score_prospect(p)
    await db.commit()
    await db.refresh(p)
    return ProspectRead.model_validate(p)


@router.patch("/{prospect_id}/stage", response_model=ProspectRead)
async def update_stage(prospect_id: UUID, data: ProspectStageUpdate, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    service = ProspectService(db)
    p = await service.update_stage(prospect_id, data.stage_id, data.position)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    return ProspectRead.model_validate(p)


@router.delete("/{prospect_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prospect(prospect_id: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    service = ProspectService(db)
    if not await service.delete(prospect_id):
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    return None


@router.post("/{prospect_id}/enrich", response_model=ProspectRead)
async def reenrich(prospect_id: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from services.scoring import score_prospect
    service = ProspectService(db)
    p = await service.reenrich(prospect_id)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    await score_prospect(p)
    await db.commit()
    await db.refresh(p)
    return ProspectRead.model_validate(p)
