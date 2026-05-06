"""Service Dashboard — agrégats."""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database.pipeline_stage import PipelineStage
from models.database.plugin_state import PluginState
from models.database.prospect import Prospect
from models.schemas.dashboard import DashboardKPI, DashboardStats, StageDistribution


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def stats(self) -> DashboardStats:
        # Total prospects
        total = (await self.db.execute(select(func.count(Prospect.id)))).scalar_one()

        # Plugins actifs
        active_plugins = (
            await self.db.execute(
                select(func.count(PluginState.id)).where(PluginState.is_active.is_(True))
            )
        ).scalar_one()

        # CA prévisionnel (somme estimated_revenue des prospects non-perdus)
        revenue_stmt = select(func.coalesce(func.sum(Prospect.estimated_revenue), 0)).select_from(
            Prospect.__table__.join(
                PipelineStage.__table__,
                Prospect.stage_id == PipelineStage.id,
                isouter=True,
            )
        ).where((PipelineStage.is_lost.is_(False)) | (PipelineStage.is_lost.is_(None)))
        revenue = (await self.db.execute(revenue_stmt)).scalar_one() or 0

        # Taux de conversion (gagné / total)
        won_count_stmt = select(func.count(Prospect.id)).join(
            PipelineStage, Prospect.stage_id == PipelineStage.id
        ).where(PipelineStage.is_won.is_(True))
        won = (await self.db.execute(won_count_stmt)).scalar_one() or 0
        conversion_rate = round((won / total) * 100, 2) if total > 0 else 0.0

        # Répartition par étape
        dist_stmt = (
            select(
                PipelineStage.id,
                PipelineStage.name,
                PipelineStage.color,
                func.count(Prospect.id),
            )
            .select_from(PipelineStage)
            .outerjoin(Prospect, Prospect.stage_id == PipelineStage.id)
            .where(PipelineStage.is_active.is_(True))
            .group_by(PipelineStage.id, PipelineStage.name, PipelineStage.color, PipelineStage.order)
            .order_by(PipelineStage.order)
        )
        dist_rows = (await self.db.execute(dist_stmt)).all()

        distribution = [
            StageDistribution(
                stage_id=str(r[0]),
                stage_name=r[1],
                color=r[2],
                count=r[3] or 0,
            )
            for r in dist_rows
        ]

        return DashboardStats(
            kpi=DashboardKPI(
                total_prospects=total,
                conversion_rate=conversion_rate,
                estimated_revenue=float(revenue),
                active_plugins=active_plugins,
            ),
            distribution=distribution,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )
