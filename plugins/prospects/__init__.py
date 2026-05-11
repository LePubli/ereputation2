"""Plugin prospects."""
from plugins.prospects.routes import router
from .bulk_routes import router as bulk_r
# puis : router.include_router(bulk_r)
__all__ = ["router"]
