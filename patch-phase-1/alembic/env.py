"""
Alembic env.py - Configuration pour migrations async
B2B Prospector - Database schema migrations
"""
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import des modèles SQLAlchemy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.prospect import Base
from core.config import settings

# Alembic Config object
config = context.config

# Override sqlalchemy.url avec DATABASE_URL des settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpréteur de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata cible pour autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Exécute les migrations en mode 'offline'.
    Aucun besoin de connexion DB réelle.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure le contexte pour les migrations online."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Exécute les migrations en mode async."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Exécute les migrations en mode 'online' avec connexion DB réelle."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
