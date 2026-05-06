"""
Configuration SQLAlchemy async + Session factory.

Utilisation :
    async with get_session() as db:
        result = await db.execute(...)

Ou en injection FastAPI :
    @router.get(...)
    async def endpoint(db: AsyncSession = Depends(get_db)):
        ...
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.config import settings

# --- Engine asynchrone ---
# NullPool en prod pour éviter les soucis de pool de connexion avec async
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    poolclass=NullPool,
    pool_pre_ping=True,
)

# --- Factory de sessions ---
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager pour usage hors FastAPI (scripts, tasks)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialise la base (ne crée pas les tables si Alembic gère)."""
    # Les migrations Alembic se chargent du schéma.
    # On peut juste tester la connexion ici.
    async with engine.begin() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))


async def close_db() -> None:
    """Ferme proprement le pool."""
    await engine.dispose()
