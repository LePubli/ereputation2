"""Service métier pipeline."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database.pipeline_stage import PipelineStage
from models.database.prospect import Prospect
from models.schemas.pipeline import (
    KanbanBoard,
    KanbanCard,
    KanbanColumn,
    PipelineStageCreate,
    PipelineStageRead,
    PipelineStageUpdate,
)


class PipelineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_stages(self) -> list[PipelineStage]:
        stmt = select(PipelineStage).where(PipelineStage.is_active.is_(True)).order_by(PipelineStage.order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_board(self) -> KanbanBoard:
        stages = await self.list_stages()
        columns: list[KanbanColumn] = []
        total = 0

        for stage in stages:
            stmt = (
                select(Prospect)
                .where(Prospect.stage_id == stage.id)
                .order_by(Prospect.stage_position, Prospect.created_at.desc())
            )
            result = await self.db.execute(stmt)
            prospects = list(result.scalars().all())

            cards = [
                KanbanCard(
                    id=p.id,
                    company_name=p.company_name,
                    siren=p.siren,
                    city=p.city,
                    propensity_category=p.propensity_category,
                    propensity_score=p.propensity_score,
                    digital_score=p.digital_score,
                    estimated_revenue=p.estimated_revenue,
                    stage_position=p.stage_position,
                    tags=p.tags or [],
                )
                for p in prospects
            ]

            columns.append(
                KanbanColumn(
                    stage=PipelineStageRead.model_validate(stage),
                    cards=cards,
                    count=len(cards),
                )
            )
            total += len(cards)

        return KanbanBoard(columns=columns, total=total)

    async def create_stage(self, data: PipelineStageCreate) -> PipelineStage:
        stage = PipelineStage(**data.model_dump())
        self.db.add(stage)
        await self.db.commit()
        await self.db.refresh(stage)
        return stage

    async def update_stage(self, stage_id: UUID, data: PipelineStageUpdate) -> PipelineStage | None:
        stmt = select(PipelineStage).where(PipelineStage.id == stage_id)
        stage = (await self.db.execute(stmt)).scalar_one_or_none()
        if not stage:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(stage, field, value)
        await self.db.commit()
        await self.db.refresh(stage)
        return stage

    async def delete_stage(self, stage_id: UUID) -> bool:
        stmt = select(PipelineStage).where(PipelineStage.id == stage_id)
        stage = (await self.db.execute(stmt)).scalar_one_or_none()
        if not stage:
            return False
        await self.db.delete(stage)
        await self.db.commit()
        return True
