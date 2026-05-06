"""
Pydantic schemas for Pipeline API.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class PipelineStageBase(BaseModel):
    """Base schema for PipelineStage."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    order: int = 0
    color: Optional[str] = "#6B7280"
    is_active: bool = True


class PipelineStageCreate(PipelineStageBase):
    """Schema for creating a PipelineStage."""
    pass


class PipelineStageResponse(PipelineStageBase):
    """Schema for PipelineStage response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    prospects_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProspectStageUpdate(BaseModel):
    """Schema for updating a prospect's stage (drag-n-drop)."""
    stage_id: int = Field(..., gt=0)
    prospect_id: int = Field(..., gt=0)


class PipelineMoveRequest(BaseModel):
    """Schema for moving a prospect in the pipeline."""
    prospect_id: int
    from_stage_id: int
    to_stage_id: int
