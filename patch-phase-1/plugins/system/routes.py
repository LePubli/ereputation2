"""
System API routes for health checks and info.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import platform
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.database import get_db
from models.database.plugin_state import PluginState
from sqlalchemy import select, func

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """System health check endpoint."""
    try:
        # Check database connection
        await db.execute(select(1))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Get active plugins count
    result = await db.execute(
        select(func.count(PluginState.id)).where(PluginState.is_active == True)
    )
    active_plugins = result.scalar() or 0
    
    return {
        "status": "healthy" if db_status == "ok" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "active_plugins": active_plugins,
        "version": "1.0.0",
    }


@router.get("/info")
async def system_info():
    """Get system information."""
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "hostname": platform.node(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@router.get("/plugins")
async def list_plugins(db: AsyncSession = Depends(get_db)):
    """List all registered plugins with their status."""
    result = await db.execute(select(PluginState).order_by(PluginState.name))
    plugins = result.scalars().all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "version": p.version,
            "is_active": p.is_active,
            "is_installed": p.is_installed,
            "last_error": p.last_error,
            "last_activated_at": p.last_activated_at.isoformat() if p.last_activated_at else None,
        }
        for p in plugins
    ]
