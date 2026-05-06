"""Alembic environment configuration (async-compatible)."""
import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import des modèles pour qu'Alembic les voie
from models.database import Base  # noqa: F401
from models.database.audit_log import AuditLog  # noqa: F401
from models.database.pipeline_stage import PipelineStage  # noqa: F401
from models.database.plugin_state import PluginState  # noqa: F401
from models.database.prospect import Contact, Prospect  # noqa: F401
from models.database.scrape_cache import ScrapeCache  # noqa: F401
from models.database.user import User  # noqa: F401

# Config Alembic
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# URL de base depuis l'env
db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://prospector:prospector@db:5432/prospector")
# Forcer asyncpg
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Exécute les migrations en mode offline (SQL généré)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Exécute les migrations en mode online async."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
