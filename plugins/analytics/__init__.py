from fastapi import APIRouter
from .routes import router as analytics_router

def create_plugin():
    r = APIRouter()
    r.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
    return r
