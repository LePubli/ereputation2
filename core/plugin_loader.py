"""
Plugin loader — Détecte et charge dynamiquement les routes des plugins.

Ce module corrige le bug de la version 1.0 où aucune route plugin n'était
chargée car le système cherchait des plugins externes inexistants.

Comportement :
- Au démarrage, scanne `plugins/` à la recherche de modules
- Pour chaque plugin actif (selon plugin_states en BDD), charge router
- Si la BDD n'est pas dispo, tombe en mode "all active" (fail-safe)
"""
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from fastapi import FastAPI

# Plugins core embarqués (toujours chargés)
CORE_PLUGINS = ["system", "prospects", "pipeline", "dashboard"]


async def load_plugins(app: "FastAPI") -> dict[str, bool]:
    """
    Charge les plugins core dans l'app FastAPI.

    Retourne un dict {plugin_name: loaded?}
    """
    loaded: dict[str, bool] = {}

    # Récupère l'état des plugins en BDD (si dispo)
    active_set = set(CORE_PLUGINS)  # par défaut tous actifs
    try:
        from sqlalchemy import select

        from core.database import AsyncSessionLocal
        from models.database.plugin_state import PluginState

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(PluginState.name).where(PluginState.is_active.is_(True))
            )
            active_set = {row[0] for row in result.all()}
            logger.info(f"Plugins actifs en BDD : {active_set}")
    except Exception as e:
        logger.warning(f"Impossible de lire plugin_states ({e}) — fallback : tous actifs")

    # Charge chaque plugin core
    for name in CORE_PLUGINS:
        if name not in active_set:
            logger.info(f"⊘ Plugin {name} désactivé en BDD — skip")
            loaded[name] = False
            continue

        try:
            module = __import__(f"plugins.{name}", fromlist=["router"])
            router = getattr(module, "router", None)
            if router is None:
                logger.error(f"✗ Plugin {name} : pas d'attribut `router`")
                loaded[name] = False
                continue

            app.include_router(router)
            logger.success(f"✓ Plugin {name} chargé ({len(router.routes)} routes)")
            loaded[name] = True

        except Exception as e:
            logger.exception(f"✗ Échec du chargement du plugin {name}: {e}")
            loaded[name] = False

    return loaded
