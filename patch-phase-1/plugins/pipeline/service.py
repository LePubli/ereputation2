"""
Pipeline service for business logic.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from models.database.pipeline_stage import PipelineStage
from models.database.prospect import Prospect
from models.schemas.pipeline import PipelineStageCreate


class PipelineService:
    """Service for pipeline operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_stages(self) -> List[PipelineStage]:
        """Get all pipeline stages ordered by position."""
        result = await self.db.execute(
            select(PipelineStage)
            .where(PipelineStage.is_active == True)
            .order_by(PipelineStage.order)
        )
        return list(result.scalars().all())
    
    async def get_stage(self, stage_id: int) -> Optional[PipelineStage]:
        """Get a stage by ID."""
        result = await self.db.execute(
            select(PipelineStage).where(PipelineStage.id == stage_id)
        )
        return result.scalar_one_or_none()
    
    async def get_prospects_by_stage(self, stage_id: int) -> List[Prospect]:
        """Get all prospects in a stage."""
        result = await self.db.execute(
            select(Prospect).where(Prospect.stage_id == stage_id)
        )
        return list(result.scalars().all())
    
    async def create_stage(self, data: PipelineStageCreate) -> PipelineStage:
        """Create a new pipeline stage."""
        stage = PipelineStage(**data.model_dump())
        self.db.add(stage)
        await self.db.flush()
        await self.db.refresh(stage)
        return stage
    
    async def get_stage_counts(self) -> Dict[int, int]:
        """Get prospect count for each stage."""
        result = await self.db.execute(
            select(PipelineStage.id, func.count(Prospect.id))
            .outerjoin(Prospect, PipelineStage.id == Prospect.stage_id)
            .group_by(PipelineStage.id)
        )
        return {row[0]: row[1] for row in result.all()}
    
    async def move_prospect(self, prospect_id: int, to_stage_id: int) -> Optional[Prospect]:
        """Move a prospect to a different stage."""
        result = await self.db.execute(
            select(Prospect).where(Prospect.id == prospect_id)
        )
        prospect = result.scalar_one_or_none()
        
        if not prospect:
            return None
        
        prospect.stage_id = to_stage_id
        await self.db.flush()
        await self.db.refresh(prospect)
        return prospect
