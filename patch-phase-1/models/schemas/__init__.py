"""
Pydantic schemas for API request/response validation.
"""
from .prospect import (
    ProspectBase,
    ProspectCreate,
    ProspectUpdate,
    ProspectResponse,
    ProspectInList,
)
from .pipeline import (
    PipelineStageBase,
    PipelineStageCreate,
    PipelineStageResponse,
    ProspectStageUpdate,
)
from .dashboard import (
    DashboardStats,
    StageDistribution,
    KPI,
)

__all__ = [
    # Prospect
    "ProspectBase",
    "ProspectCreate",
    "ProspectUpdate",
    "ProspectResponse",
    "ProspectInList",
    # Pipeline
    "PipelineStageBase",
    "PipelineStageCreate",
    "PipelineStageResponse",
    "ProspectStageUpdate",
    # Dashboard
    "DashboardStats",
    "StageDistribution",
    "KPI",
]
