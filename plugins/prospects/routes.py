"""Routes REST du plugin prospects."""
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

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

router = APIRouter(prefix="/api/v1/prospects", tags=["prospects"])


@router.get("", response_model=ProspectListResponse)
async def list_prospects(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = Query(None),
    stage_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = ProspectService(db)
    items, total = await service.list_prospects(
        page=page, page_size=page_size, search=search, stage_id=stage_id
    )
    return ProspectListResponse(
        items=[ProspectRead.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ProspectRead, status_code=status.HTTP_201_CREATED)
async def create_manual(
    data: ProspectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Création manuelle d'un prospect (formulaire complet)."""
    service = ProspectService(db)
    prospect = await service.create_manual(data)
    return ProspectRead.model_validate(prospect)


@router.post("/by-siret", response_model=ProspectRead, status_code=status.HTTP_201_CREATED)
async def create_by_siret(
    data: ProspectCreateBySiret,
    db: AsyncSession = Depends(get_db),
):
    """Création par SIREN/SIRET avec scraping multi-sources automatique."""
    service = ProspectService(db)
    try:
        prospect = await service.create_by_identifier(data.identifier)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        # Log complet + message utilisateur clair (pas de 502 silencieux)
        import traceback
        error_detail = str(e)
        # Si toutes les sources ont échoué (403/400), on le dit clairement
        if "sources_used" in error_detail or "scraping" in error_detail.lower():
            msg = "Enrichissement impossible : sources externes indisponibles. Essayez la saisie manuelle."
        else:
            msg = f"Échec de l'enrichissement : {error_detail[:200]}"
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=msg)
    return ProspectRead.model_validate(prospect)


@router.post("/import", response_model=ProspectImportResult)
async def import_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Import en masse depuis CSV/XLS/XLSX."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Fichier sans nom")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fichier > 10 MB")

    service = ProspectService(db)
    return await service.import_from_file(contents, file.filename)


@router.get("/{prospect_id}", response_model=ProspectRead)
async def get_prospect(
    prospect_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = ProspectService(db)
    prospect = await service.get_prospect(prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    return ProspectRead.model_validate(prospect)


@router.patch("/{prospect_id}", response_model=ProspectRead)
async def update_prospect(
    prospect_id: UUID,
    data: ProspectUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = ProspectService(db)
    prospect = await service.update(prospect_id, data)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    return ProspectRead.model_validate(prospect)


@router.patch("/{prospect_id}/stage", response_model=ProspectRead)
async def update_prospect_stage(
    prospect_id: UUID,
    data: ProspectStageUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Drag-n-drop Kanban : changer l'étape d'un prospect."""
    service = ProspectService(db)
    prospect = await service.update_stage(prospect_id, data.stage_id, data.position)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    return ProspectRead.model_validate(prospect)


@router.delete("/{prospect_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prospect(
    prospect_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = ProspectService(db)
    deleted = await service.delete(prospect_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    return None


@router.post("/{prospect_id}/enrich", response_model=ProspectRead)
async def reenrich_prospect(
    prospect_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Force un re-scraping multi-sources et met à jour le prospect."""
    service = ProspectService(db)
    prospect = await service.reenrich(prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect introuvable")
    return ProspectRead.model_validate(prospect)
