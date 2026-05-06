"""Schémas Pydantic pour le pipeline Kanban."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PipelineStageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    color: str = Field("#3b82f6", max_length=20)
    order: int = 0
    is_won: bool = False
    is_lost: bool = False
    is_active: bool = True


class PipelineStageCreate(PipelineStageBase):
    pass


class PipelineStageUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    order: int | None = None
    is_active: bool | None = None


class PipelineStageRead(PipelineStageBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class KanbanCard(BaseModel):
    """Carte simplifiée pour l'affichage Kanban."""
    id: UUID
    company_name: str
    siren: str | None
    city: str | None
    propensity_category: str | None
    propensity_score: float | None
    digital_score: float | None
    estimated_revenue: float | None
    stage_position: int
    tags: list[str] = Field(default_factory=list)


class KanbanColumn(BaseModel):
    """Colonne du Kanban avec ses cartes."""
    stage: PipelineStageRead
    cards: list[KanbanCard]
    count: int


class KanbanBoard(BaseModel):
    """Représentation complète du Kanban."""
    columns: list[KanbanColumn]
    total: int
