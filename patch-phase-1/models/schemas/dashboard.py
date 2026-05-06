"""
Pydantic schemas for Dashboard API.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class KPI(BaseModel):
    """Key Performance Indicator."""
    label: str
    value: float
    unit: str = ""
    change: Optional[float] = None  # Percentage change
    trend: Optional[str] = None  # "up", "down", "neutral"


class StageDistribution(BaseModel):
    """Distribution of prospects by pipeline stage."""
    stage_id: int
    stage_name: str
    count: int
    percentage: float
    color: Optional[str] = "#6B7280"


class DashboardStats(BaseModel):
    """Dashboard statistics response."""
    total_prospects: int = 0
    new_prospects_today: int = 0
    new_prospects_week: int = 0
    conversion_rate: float = 0.0  # Percentage
    predicted_revenue: float = 0.0
    active_plugins: int = 0
    
    # KPIs
    kpis: List[KPI] = []
    
    # Stage distribution for donut chart
    stage_distribution: List[StageDistribution] = []
    
    # Recent activity
    recent_prospects_count: int = 0
    deals_won_this_month: int = 0
    deals_lost_this_month: int = 0
