"""
Pipeline plugin for B2B Prospector.
"""
from .routes import router
from .service import PipelineService

__all__ = ["router", "PipelineService"]
