"""
Prospects API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.database import get_db
from models.schemas.prospect import (
    ProspectCreate,
    ProspectUpdate,
    ProspectResponse,
    ProspectInList,
)
from .service import ProspectService

router = APIRouter(prefix="/api/v1/prospects", tags=["prospects"])


@router.get("", response_model=List[ProspectInList])
async def list_prospects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query: Optional[str] = None,
    stage_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of prospects."""
    service = ProspectService(db)
    prospects, total = await service.get_prospects(
        page=page, page_size=page_size, query=query, stage_id=stage_id
    )
    return prospects


@router.get("/{prospect_id}", response_model=ProspectResponse)
async def get_prospect(prospect_id: int, db: AsyncSession = Depends(get_db)):
    """Get a prospect by ID."""
    service = ProspectService(db)
    prospect = await service.get_prospect(prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return prospect


@router.post("", response_model=ProspectResponse)
async def create_prospect(data: ProspectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new prospect."""
    service = ProspectService(db)
    
    # If SIREN provided, try to fetch from INSEE
    if data.siren:
        insee_data = await service.fetch_from_insee(data.siren)
        if insee_data:
            # Merge INSEE data with provided data
            merged_data = {**data.model_dump(), **insee_data}
            data = ProspectCreate(**merged_data)
    
    prospect = await service.create_prospect(data)
    return prospect


@router.put("/{prospect_id}", response_model=ProspectResponse)
async def update_prospect(
    prospect_id: int,
    data: ProspectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing prospect."""
    service = ProspectService(db)
    prospect = await service.update_prospect(prospect_id, data)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return prospect


@router.delete("/{prospect_id}")
async def delete_prospect(prospect_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a prospect."""
    service = ProspectService(db)
    success = await service.delete_prospect(prospect_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return {"message": "Prospect deleted successfully"}


@router.patch("/{prospect_id}/stage")
async def update_prospect_stage(
    prospect_id: int,
    stage_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Update prospect stage (for Kanban drag-n-drop)."""
    service = ProspectService(db)
    prospect = await service.update_stage(prospect_id, stage_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return prospect
