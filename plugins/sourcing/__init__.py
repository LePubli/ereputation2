from fastapi import APIRouter
from .routes import router as sourcing_router

def create_plugin():
    r = APIRouter()
    r.include_router(sourcing_router, prefix="/sourcing", tags=["sourcing"])
    return r
