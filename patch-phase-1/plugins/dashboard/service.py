"""
Dashboard service for business logic.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from models.database.prospect import Prospect
from models.database.pipeline_stage import PipelineStage
from models.database.plugin_state import PluginState
from models.schemas.dashboard import DashboardStats, KPI, StageDistribution


class DashboardService:
    """Service for dashboard operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_stats(self) -> DashboardStats:
        """Get dashboard statistics."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Total prospects
        total_result = await self.db.execute(select(func.count(Prospect.id)))
        total_prospects = total_result.scalar() or 0
        
        # New prospects today
        today_result = await self.db.execute(
            select(func.count(Prospect.id)).where(Prospect.created_at >= today_start)
        )
        new_today = today_result.scalar() or 0
        
        # New prospects this week
        week_result = await self.db.execute(
            select(func.count(Prospect.id)).where(Prospect.created_at >= week_start)
        )
        new_week = week_result.scalar() or 0
        
        # Active plugins
        plugins_result = await self.db.execute(
            select(func.count(PluginState.id)).where(PluginState.is_active == True)
        )
        active_plugins = plugins_result.scalar() or 0
        
        # Get stage distribution
        stages = await self._get_stage_distribution()
        
        # Calculate conversion rate (won / total)
        won_stage = await self.db.execute(
            select(PipelineStage.id).where(PipelineStage.name.ilike("%gagné%"))
        )
        won_stage_id = won_stage.scalar_one_or_none()
        
        conversion_rate = 0.0
        deals_won = 0
        if won_stage_id:
            won_result = await self.db.execute(
                select(func.count(Prospect.id)).where(Prospect.stage_id == won_stage_id)
            )
            deals_won = won_result.scalar() or 0
            if total_prospects > 0:
                conversion_rate = (deals_won / total_prospects) * 100
        
        # Build KPIs
        kpis = [
            KPI(label="Total Prospects", value=total_prospects, unit="", trend="up"),
            KPI(label="Nouveaux (7j)", value=new_week, unit="", change=round((new_week - new_today) / max(new_today, 1) * 100, 1)),
            KPI(label="Taux de conversion", value=round(conversion_rate, 1), unit="%"),
            KPI(label="Plugins actifs", value=active_plugins, unit=""),
        ]
        
        return DashboardStats(
            total_prospects=total_prospects,
            new_prospects_today=new_today,
            new_prospects_week=new_week,
            conversion_rate=round(conversion_rate, 2),
            active_plugins=active_plugins,
            kpis=kpis,
            stage_distribution=stages,
            deals_won_this_month=deals_won,
        )
    
    async def _get_stage_distribution(self) -> List[StageDistribution]:
        """Get prospect distribution by stage."""
        result = await self.db.execute(
            select(
                PipelineStage.id,
                PipelineStage.name,
                PipelineStage.color,
                func.count(Prospect.id).label("count")
            )
            .outerjoin(Prospect, PipelineStage.id == Prospect.stage_id)
            .group_by(PipelineStage.id, PipelineStage.name, PipelineStage.color)
            .order_by(PipelineStage.order)
        )
        
        rows = result.all()
        total = sum(row[2] for row in rows) or 1
        
        return [
            StageDistribution(
                stage_id=row[0],
                stage_name=row[1],
                count=row[2],
                percentage=round((row[2] / total) * 100, 1),
                color=row[3] or "#6B7280",
            )
            for row in rows
        ]
