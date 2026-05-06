"""Routes REST du plugin dashboard."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.schemas.dashboard import DashboardStats
from plugins.dashboard.service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    service = DashboardService(db)
    return await service.stats()
