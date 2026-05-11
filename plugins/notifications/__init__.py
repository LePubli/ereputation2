from fastapi import APIRouter
from .routes import router as notifications_router

def create_plugin():
    r = APIRouter()
    r.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
    return r
