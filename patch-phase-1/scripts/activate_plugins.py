#!/usr/bin/env python3
"""
Script d'activation des plugins par défaut.
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from models.database.plugin_state import PluginState

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/prospector"
)


async def activate_plugins():
    """Activate default plugins."""
    print(f"🔌 Connexion à {DATABASE_URL}...")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Liste des plugins à activer
        plugins_to_activate = [
            ("prospects", "Prospects Management"),
            ("pipeline", "Pipeline Kanban"),
            ("dashboard", "Dashboard"),
            ("system", "System"),
        ]
        
        for pname, display in plugins_to_activate:
            result = await session.execute(
                select(PluginState).where(PluginState.name == pname)
            )
            plugin = result.scalar_one_or_none()
            
            if plugin:
                plugin.is_active = True
                print(f"✅ Plugin '{pname}' activé")
            else:
                plugin = PluginState(
                    name=pname,
                    display_name=display,
                    version="1.0.0",
                    is_active=True,
                    is_installed=True,
                    config={}
                )
                session.add(plugin)
                print(f"✅ Plugin '{pname}' créé et activé")
        
        await session.commit()
        print("\n🎉 Plugins activés avec succès!")


if __name__ == "__main__":
    asyncio.run(activate_plugins())
