"""Routes système — health, info, gestion des plugins."""
import time
from datetime import datetime, timezone

import redis.asyncio as redis_lib
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from models.database.plugin_state import PluginState
from models.schemas.dashboard import SystemInfo

router = APIRouter(prefix="/api/v1", tags=["system"])

_START_TIME = time.time()


# =============================================================================
# /system/health  &  /system/info
# =============================================================================

@router.get("/system/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Healthcheck pour Coolify / Docker / Kubernetes."""
    db_ok = False
    redis_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"DB health failed: {e}")

    try:
        client = redis_lib.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
        redis_ok = True
    except Exception as e:
        logger.error(f"Redis health failed: {e}")

    status = "healthy" if (db_ok and redis_ok) else "degraded" if (db_ok or redis_ok) else "unhealthy"

    return {
        "status": status,
        "checks": {
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/system/info", response_model=SystemInfo)
async def system_info(db: AsyncSession = Depends(get_db)):
    """Informations système consolidées (page Paramètres)."""
    db_ok = False
    redis_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    try:
        client = redis_lib.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
        redis_ok = True
    except Exception:
        pass

    # Plugins actifs
    stmt = select(PluginState).where(PluginState.is_active.is_(True))
    result = await db.execute(stmt)
    active_plugins = [p.name for p in result.scalars().all()]

    total_count_stmt = select(PluginState)
    total = len((await db.execute(total_count_stmt)).scalars().all())

    return SystemInfo(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        status="healthy" if (db_ok and redis_ok) else "degraded",
        uptime_seconds=int(time.time() - _START_TIME),
        plugins_count=total,
        plugins_active=active_plugins,
        database="ok" if db_ok else "error",
        redis="ok" if redis_ok else "error",
    )


# =============================================================================
# /system/plugins
# =============================================================================

@router.get("/system/plugins")
async def list_plugins(db: AsyncSession = Depends(get_db)):
    """Liste tous les plugins (état persisté en BDD)."""
    stmt = select(PluginState).order_by(PluginState.name)
    result = await db.execute(stmt)
    plugins = result.scalars().all()
    return {
        "plugins": [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "active": p.is_active,
                "config": p.config or {},
            }
            for p in plugins
        ],
        "total": len(plugins),
        "active_count": sum(1 for p in plugins if p.is_active),
    }


@router.post("/system/plugins/{name}/toggle")
async def toggle_plugin(name: str, db: AsyncSession = Depends(get_db)):
    """Active/désactive un plugin (changement effectif au prochain restart)."""
    stmt = select(PluginState).where(PluginState.name == name)
    plugin = (await db.execute(stmt)).scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin {name} introuvable")

    plugin.is_active = not plugin.is_active
    await db.commit()

    return {
        "name": plugin.name,
        "active": plugin.is_active,
        "message": f"Plugin {name} {'activé' if plugin.is_active else 'désactivé'} (effet au prochain redémarrage)",
    }
