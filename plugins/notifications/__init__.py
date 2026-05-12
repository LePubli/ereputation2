from .ws_routes import router
__all__ = ["router"]

def create_plugin():
    r = APIRouter()
    r.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
    return r
