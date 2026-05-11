from fastapi import APIRouter
from .routes import router as export_router

def create_plugin():
    r = APIRouter()
    r.include_router(export_router, prefix="/export", tags=["export"])
    return r
