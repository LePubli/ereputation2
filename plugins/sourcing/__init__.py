from fastapi import APIRouter
from .routes import router as _r

router = APIRouter()
router.include_router(_r, prefix="/api/v1/sourcing", tags=["sourcing"])
__all__ = ["router"]
