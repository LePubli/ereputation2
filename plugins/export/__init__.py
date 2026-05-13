from fastapi import APIRouter
from .routes import router as _r

router = APIRouter()
router.include_router(_r, prefix="/api/v1/export", tags=["export"])
__all__ = ["router"]
