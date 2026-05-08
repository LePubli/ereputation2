"""Plugin loader Phase 3."""
from typing import TYPE_CHECKING
from loguru import logger
if TYPE_CHECKING:
    from fastapi import FastAPI

CORE_PLUGINS = ["auth", "system", "prospects", "pipeline", "dashboard", "activities", "agent", "webhooks"]

async def load_plugins(app: "FastAPI") -> dict[str, bool]:
    loaded: dict[str, bool] = {}
    active_set = set(CORE_PLUGINS)
    try:
        from sqlalchemy import select
        from core.database import AsyncSessionLocal
        from models.database.plugin_state import PluginState
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(PluginState.name).where(PluginState.is_active.is_(True)))
            active_set = {row[0] for row in result.all()} | {"auth","activities","agent","webhooks"}
    except Exception as e:
        logger.warning(f"plugin_states indisponible ({e})")
    for name in CORE_PLUGINS:
        if name not in active_set:
            loaded[name] = False
            continue
        try:
            module = __import__(f"plugins.{name}", fromlist=["router"])
            r = getattr(module, "router", None)
            if r is None:
                loaded[name] = False
                continue
            app.include_router(r)
            logger.success(f"✓ Plugin {name} ({len(r.routes)} routes)")
            loaded[name] = True
        except Exception as e:
            logger.exception(f"✗ Plugin {name}: {e}")
            loaded[name] = False
    return loaded
