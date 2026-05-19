"""Routes système — gestion plugins WordPress-like + thèmes."""
import time
from datetime import datetime, timezone
from pathlib import Path

import redis.asyncio as redis_lib
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from models.database.plugin_state import PluginState
from core.plugin_registry import registry, load_manifest

router = APIRouter(prefix="/api/v1", tags=["system"])
_START_TIME = time.time()


@router.get("/system/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_ok = redis_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"DB health: {e}")
    try:
        client = redis_lib.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
        redis_ok = True
    except Exception as e:
        logger.error(f"Redis health: {e}")

    status = "healthy" if (db_ok and redis_ok) else "degraded" if (db_ok or redis_ok) else "unhealthy"
    return {
        "status": status,
        "uptime_seconds": round(time.time() - _START_TIME),
        "checks": {"database": "ok" if db_ok else "error", "redis": "ok" if redis_ok else "error"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/system/plugins")
async def list_plugins(
    current_user=Depends(lambda: None),
    db: AsyncSession = Depends(get_db),
):
    """Liste TOUS les plugins avec leur état, manifest et config."""
    from core.plugin_loader import ALL_PLUGINS, CORE_PLUGINS

    # Charge les états DB
    db_states = {}
    try:
        rows = (await db.execute(select(PluginState))).scalars().all()
        db_states = {r.name: r for r in rows}
    except Exception:
        pass

    plugins = []
    for folder_name in ALL_PLUGINS:
        manifest = registry.get_manifest(folder_name) or load_manifest(folder_name)
        db_state = db_states.get(folder_name)
        is_core = folder_name in CORE_PLUGINS

        plugins.append({
            "name": folder_name,
            "display_name": manifest.get("display_name") or manifest.get("name") or folder_name,
            "version": db_state.version if db_state else manifest.get("version", "1.0.0"),
            "description": db_state.description if db_state else manifest.get("description", ""),
            "author": manifest.get("author", "B2B Prospector"),
            "category": manifest.get("category", "tools"),
            "icon": manifest.get("icon", "🔌"),
            "is_active": registry.is_active(folder_name),
            "is_core": is_core,
            "is_loaded": folder_name in registry._routers,
            "config": db_state.config if db_state else {},
            "dependencies": manifest.get("dependencies", []),
            "permissions": manifest.get("permissions", []),
        })

    return {
        "items": plugins,
        "total": len(plugins),
        "active": sum(1 for p in plugins if p["is_active"]),
        "inactive": sum(1 for p in plugins if not p["is_active"]),
    }


@router.post("/system/plugins/{name}/toggle")
async def toggle_plugin(
    name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Active/désactive un plugin instantanément (hot-reload).
    Aucun restart requis.
    """
    from core.plugin_loader import CORE_PLUGINS
    from core.plugin_loader import toggle_plugin as _toggle

    if name in CORE_PLUGINS:
        raise HTTPException(400, f"Le plugin '{name}' est core et ne peut pas être désactivé")

    new_state = not registry.is_active(name)

    # 1. Mise à jour in-memory (instantané)
    _toggle(name, new_state)

    # 2. Persistance DB
    db_state = (await db.execute(select(PluginState).where(PluginState.name == name))).scalar_one_or_none()
    if db_state:
        db_state.is_active = new_state
    else:
        manifest = load_manifest(name)
        db_state = PluginState(
            name=name,
            version=manifest.get("version", "1.0.0"),
            description=manifest.get("description", ""),
            is_active=new_state,
            config={},
        )
        db.add(db_state)

    await db.commit()

    action = "activé" if new_state else "désactivé"
    logger.info(f"[System] Plugin '{name}' {action} (hot-reload)")

    return {
        "name": name,
        "is_active": new_state,
        "message": f"Plugin '{name}' {action} instantanément",
        "hot_reload": True,
    }


@router.patch("/system/plugins/{name}/config")
async def update_plugin_config(
    name: str,
    config: dict,
    db: AsyncSession = Depends(get_db),
):
    """Met à jour la configuration d'un plugin."""
    db_state = (await db.execute(select(PluginState).where(PluginState.name == name))).scalar_one_or_none()
    if not db_state:
        raise HTTPException(404, f"Plugin '{name}' introuvable en DB")

    db_state.config = {**db_state.config, **config}
    await db.commit()

    return {"name": name, "config": db_state.config, "message": "Configuration mise à jour"}


@router.get("/system/plugins/{name}")
async def get_plugin(name: str, db: AsyncSession = Depends(get_db)):
    """Détails complets d'un plugin."""
    manifest = registry.get_manifest(name) or load_manifest(name)
    db_state = (await db.execute(select(PluginState).where(PluginState.name == name))).scalar_one_or_none()
    router_obj = registry.get_router(name)

    routes = []
    if router_obj:
        for route in router_obj.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({"path": route.path, "methods": list(route.methods or [])})

    return {
        "name": name,
        "manifest": manifest,
        "is_active": registry.is_active(name),
        "is_loaded": name in registry._routers,
        "config": db_state.config if db_state else {},
        "routes": routes,
        "routes_count": len(routes),
    }
