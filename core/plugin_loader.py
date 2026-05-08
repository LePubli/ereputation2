"""Plugin loader Phase 2 — charge auth + activities en plus des core."""
from typing import TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from fastapi import FastAPI

CORE_PLUGINS = ["auth", "system", "prospects", "pipeline", "dashboard", "activities"]


async def load_plugins(app: "FastAPI") -> dict[str, bool]:
    loaded: dict[str, bool] = {}
    active_set = set(CORE_PLUGINS)

    try:
        from sqlalchemy import select
        from core.database import AsyncSessionLocal
        from models.database.plugin_state import PluginState

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(PluginState.name).where(PluginState.is_active.is_(True))
            )
            db_active = {row[0] for row in result.all()}
            # Auth et activities toujours actifs (sécurité)
            active_set = db_active | {"auth", "activities"}
    except Exception as e:
        logger.warning(f"Lecture plugin_states impossible ({e}) — fallback")

    for name in CORE_PLUGINS:
        if name not in active_set:
            loaded[name] = False
            continue
        try:
            module = __import__(f"plugins.{name}", fromlist=["router"])
            router = getattr(module, "router", None)
            if router is None:
                loaded[name] = False
                continue
            app.include_router(router)
            logger.success(f"✓ Plugin {name} chargé ({len(router.routes)} routes)")
            loaded[name] = True
        except Exception as e:
            logger.exception(f"✗ Plugin {name} : {e}")
            loaded[name] = False

    return loaded
