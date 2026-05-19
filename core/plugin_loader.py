"""
Plugin Loader v2 — WordPress-like hot-reload.

Stratégie :
1. Charge TOUS les plugins au démarrage (actifs ou non)
2. Middleware bloque les routes des plugins inactifs
3. Toggle = DB + in-memory registry → instantané, zéro restart
"""
from typing import TYPE_CHECKING
from pathlib import Path
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.plugin_registry import registry, load_manifest, load_plugin_module

if TYPE_CHECKING:
    from fastapi import FastAPI

# ── Core (toujours actifs, non désactivables) ──
CORE_PLUGINS = {"auth", "system", "notifications"}

# ── Tous les plugins disponibles ──
ALL_PLUGINS = [
    # Core
    "auth", "system", "notifications",
    # CRM
    "prospects", "pipeline", "dashboard", "activities",
    "analytics", "export",
    # Sourcing
    "sourcing", "signals", "inbound",
    # Marketing
    "sequencer", "abm", "crm_sync", "webhooks",
    # Intelligence
    "agent", "contacts",
    # Plugins avancés (dossiers avec tirets gérés)
    "predictive-scorer", "ab-testing",
    "outreach-multichannel", "automation-engine",
    # Thèmes
    "themes",
]

# Map : préfixe de route → nom plugin (pour le middleware)
ROUTE_PLUGIN_MAP: dict[str, str] = {
    "/api/v1/prospects": "prospects",
    "/api/v1/pipeline": "pipeline",
    "/api/v1/dashboard": "dashboard",
    "/api/v1/activities": "activities",
    "/api/v1/analytics": "analytics",
    "/api/v1/export": "export",
    "/api/v1/sourcing": "sourcing",
    "/api/v1/signals": "signals",
    "/api/v1/inbound": "inbound",
    "/api/v1/sequencer": "sequencer",
    "/api/v1/abm": "abm",
    "/api/v1/crm-sync": "crm_sync",
    "/api/v1/webhooks": "webhooks",
    "/api/v1/ai": "agent",
    "/api/v1/contacts": "contacts",
    "/api/v1/scorer": "predictive-scorer",
    "/api/v1/ab-testing": "ab-testing",
    "/api/v1/outreach": "outreach-multichannel",
    "/api/v1/automation": "automation-engine",
    "/api/v1/themes": "themes",
}


class PluginGateMiddleware(BaseHTTPMiddleware):
    """
    Middleware hot-reload — bloque les routes des plugins inactifs.
    Vérifie le registry in-memory (O(1), zéro DB query).
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Vérifie si la route appartient à un plugin inactif
        for prefix, plugin_name in ROUTE_PLUGIN_MAP.items():
            if path.startswith(prefix):
                if plugin_name not in CORE_PLUGINS and not registry.is_active(plugin_name):
                    return JSONResponse(
                        status_code=404,
                        content={
                            "detail": f"Plugin '{plugin_name}' est désactivé.",
                            "plugin": plugin_name,
                            "code": "plugin_disabled",
                        },
                    )
                break

        return await call_next(request)


async def load_plugins(app: "FastAPI") -> dict[str, bool]:
    """
    Charge TOUS les plugins + initialise le registry depuis la DB.
    Le middleware PluginGateMiddleware est déjà ajouté au niveau de main.py.
    """
    loaded: dict[str, bool] = {}

    # 1. Charge l'état depuis la DB
    await _sync_registry_from_db()

    # 2. Le middleware a déjà été ajouté dans main.py via le paramètre middleware=
    # Pas besoin d'appeler app.add_middleware() ici (provoquerait une erreur)

    # 3. Charge TOUS les plugins (actifs ET inactifs)
    for folder_name in ALL_PLUGINS:
        module_name = folder_name.replace("-", "_")
        manifest = load_manifest(folder_name)
        registry.register_manifest(folder_name, manifest)

        try:
            module = load_plugin_module(folder_name)
            if module is None:
                loaded[folder_name] = False
                continue

            router = getattr(module, "router", None)
            if router is None:
                loaded[folder_name] = False
                continue

            app.include_router(router)
            registry.register_router(folder_name, router)

            is_active = registry.is_active(folder_name)
            status = "✓" if is_active else "○"
            logger.success(f"{status} Plugin {folder_name} ({len(router.routes)} routes) {'[ACTIF]' if is_active else '[INACTIF]'}")
            loaded[folder_name] = True

        except Exception as e:
            logger.error(f"✗ Plugin {folder_name}: {e}")
            loaded[folder_name] = False

    return loaded


async def _sync_registry_from_db():
    """Synchronise le registry in-memory depuis la DB."""
    try:
        from sqlalchemy import select
        from core.database import AsyncSessionLocal
        from models.database.plugin_state import PluginState

        async with AsyncSessionLocal() as db:
            rows = (await db.execute(select(PluginState))).scalars().all()
            db_states = {r.name: r.is_active for r in rows}

        for plugin_name in ALL_PLUGINS:
            if plugin_name in CORE_PLUGINS:
                registry.activate(plugin_name)
            elif plugin_name in db_states:
                if db_states[plugin_name]:
                    registry.activate(plugin_name)
                else:
                    registry.deactivate(plugin_name)
            else:
                # Nouveau plugin non en DB → actif par défaut
                registry.activate(plugin_name)

        logger.info(f"[Registry] {len(registry.active_plugins)} plugins actifs en mémoire")

    except Exception as e:
        logger.warning(f"[Registry] Sync DB échouée ({e}) — tous actifs par défaut")
        for plugin_name in ALL_PLUGINS:
            registry.activate(plugin_name)


def toggle_plugin(name: str, active: bool) -> None:
    """Toggle instantané — met à jour le registry in-memory."""
    if name in CORE_PLUGINS:
        raise ValueError(f"Le plugin '{name}' est core et ne peut pas être désactivé.")
    if active:
        registry.activate(name)
    else:
        registry.deactivate(name)
    logger.info(f"[Registry] Plugin '{name}' → {'actif' if active else 'inactif'}")
