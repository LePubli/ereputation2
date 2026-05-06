"""
Dashboard plugin for B2B Prospector.
"""
from .routes import router
from .service import DashboardService

__all__ = ["router", "DashboardService"]
