"""
Pipeline API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.database import get_db
from models.schemas.pipeline import PipelineStageResponse, PipelineStageCreate, PipelineMoveRequest
from .service import PipelineService

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


@router.get("/stages", response_model=List[PipelineStageResponse])
async def get_pipeline_stages(db: AsyncSession = Depends(get_db)):
    """Get all pipeline stages with prospect counts."""
    service = PipelineService(db)
    stages = await service.get_stages()
    counts = await service.get_stage_counts()
    
    result = []
    for stage in stages:
        stage_dict = {
            "id": stage.id,
            "name": stage.name,
            "description": stage.description,
            "order": stage.order,
            "color": stage.color,
            "is_active": stage.is_active,
            "prospects_count": counts.get(stage.id, 0),
        }
        result.append(stage_dict)
    
    return result


@router.get("/stages/{stage_id}/prospects")
async def get_stage_prospects(stage_id: int, db: AsyncSession = Depends(get_db)):
    """Get all prospects in a specific stage."""
    service = PipelineService(db)
    stage = await service.get_stage(stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    prospects = await service.get_prospects_by_stage(stage_id)
    return prospects


@router.post("/stages", response_model=PipelineStageResponse)
async def create_stage(data: PipelineStageCreate, db: AsyncSession = Depends(get_db)):
    """Create a new pipeline stage."""
    service = PipelineService(db)
    return await service.create_stage(data)


@router.patch("/move")
async def move_prospect(
    data: PipelineMoveRequest,
    db: AsyncSession = Depends(get_db),
):
    """Move a prospect to a different stage (drag-n-drop)."""
    service = PipelineService(db)
    prospect = await service.move_prospect(data.prospect_id, data.to_stage_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return {"message": "Prospect moved successfully", "prospect_id": prospect.id}
