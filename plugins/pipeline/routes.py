"""Routes REST du plugin pipeline."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.schemas.pipeline import (
    KanbanBoard,
    PipelineStageCreate,
    PipelineStageRead,
    PipelineStageUpdate,
)
from plugins.pipeline.service import PipelineService

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


@router.get("/board", response_model=KanbanBoard)
async def get_board(db: AsyncSession = Depends(get_db)):
    """Récupère le Kanban complet (colonnes + cartes)."""
    service = PipelineService(db)
    return await service.get_board()


@router.get("/stages", response_model=list[PipelineStageRead])
async def list_stages(db: AsyncSession = Depends(get_db)):
    service = PipelineService(db)
    stages = await service.list_stages()
    return [PipelineStageRead.model_validate(s) for s in stages]


@router.post("/stages", response_model=PipelineStageRead, status_code=status.HTTP_201_CREATED)
async def create_stage(
    data: PipelineStageCreate,
    db: AsyncSession = Depends(get_db),
):
    service = PipelineService(db)
    stage = await service.create_stage(data)
    return PipelineStageRead.model_validate(stage)


@router.patch("/stages/{stage_id}", response_model=PipelineStageRead)
async def update_stage(
    stage_id: UUID,
    data: PipelineStageUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = PipelineService(db)
    stage = await service.update_stage(stage_id, data)
    if not stage:
        raise HTTPException(status_code=404, detail="Étape introuvable")
    return PipelineStageRead.model_validate(stage)


@router.delete("/stages/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stage(
    stage_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = PipelineService(db)
    deleted = await service.delete_stage(stage_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Étape introuvable")
    return None
