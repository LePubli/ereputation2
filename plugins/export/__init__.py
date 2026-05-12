from fastapi import APIRouter
from .routes import router as _r

router = APIRouter()
router.include_router(_r, prefix="/export", tags=["export"])
__all__ = ["router"]
