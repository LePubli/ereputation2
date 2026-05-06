"""Schémas Pydantic pour le dashboard."""
from pydantic import BaseModel


class StageDistribution(BaseModel):
    stage_id: str
    stage_name: str
    color: str
    count: int


class DashboardKPI(BaseModel):
    total_prospects: int
    conversion_rate: float
    estimated_revenue: float
    active_plugins: int


class DashboardStats(BaseModel):
    kpi: DashboardKPI
    distribution: list[StageDistribution]
    last_updated: str  # ISO format


class SystemInfo(BaseModel):
    app_name: str
    app_version: str
    status: str  # "healthy" | "degraded" | "unhealthy"
    uptime_seconds: int
    plugins_count: int
    plugins_active: list[str]
    database: str  # "ok" | "error"
    redis: str
