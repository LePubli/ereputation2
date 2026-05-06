"""
Script utilitaire — force l'activation des plugins core.

Usage : python -m scripts.activate_plugins
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger  # noqa: E402
from sqlalchemy import select  # noqa: E402

from core.database import AsyncSessionLocal, close_db  # noqa: E402
from models.database.plugin_state import PluginState  # noqa: E402

CORE_PLUGINS = ["system", "prospects", "pipeline", "dashboard"]


async def main() -> None:
    async with AsyncSessionLocal() as db:
        for name in CORE_PLUGINS:
            stmt = select(PluginState).where(PluginState.name == name)
            plugin = (await db.execute(stmt)).scalar_one_or_none()
            if not plugin:
                logger.warning(f"Plugin {name} introuvable en BDD")
                continue
            if not plugin.is_active:
                plugin.is_active = True
                logger.info(f"✓ Plugin {name} activé")
        await db.commit()
    await close_db()
    logger.success("✅ Plugins core actifs")


if __name__ == "__main__":
    asyncio.run(main())
