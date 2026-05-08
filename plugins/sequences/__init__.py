"""Plugin sequences - Phase 4."""
from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/sequences", tags=["sequences"])
__all__ = ["router"]
