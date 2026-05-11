"""Plugin loader Phase 4 — tous les plugins inclus."""
from typing import TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from fastapi import FastAPI

CORE_PLUGINS = [
    "auth", "system", "prospects", "pipeline", "dashboard",
    "activities", "agent", "webhooks",
    # Phase 4
    "sequencer", "signals", "inbound", "abm", "crm_sync",
    "analytics", "sourcing", "export", "notifications",
]

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
            # Ces plugins sont toujours actifs (sécurité / infrastructure)
            always_active = {
    "auth", "system", "sequencer", "signals", "inbound",
    "abm", "crm_sync",
    # Phase 5-6
    "analytics", "sourcing", "export", "notifications",
}
            active_set = db_active | always_active
    except Exception as e:
        logger.warning(f"plugin_states indisponible ({e}) — tous actifs par défaut")

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
