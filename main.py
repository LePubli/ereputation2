"""
Point d'entrée FastAPI — B2B Prospector.

Lance avec :
    uvicorn main:app --host 0.0.0.0 --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from core.config import settings
from core.database import close_db, init_db
from core.plugin_loader import load_plugins


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cycle de vie de l'application."""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} — démarrage")

    # 1. Test BDD
    try:
        await init_db()
        logger.success("✓ Base de données connectée")
    except Exception as e:
        logger.error(f"✗ DB non disponible : {e}")

    # 2. Chargement plugins
    loaded = await load_plugins(app)
    active = [k for k, v in loaded.items() if v]
    logger.info(f"📦 Plugins actifs : {', '.join(active) or 'aucun'}")

    yield

    logger.info("👋 Arrêt de l'application")
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket notifications (après app défini)
from plugins.notifications.ws_routes import router as ws_router
app.include_router(ws_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/system/health",
    }


@app.get("/health")
async def root_health():
    """Health basique sans dépendance BDD (pour Docker healthcheck)."""
    return {"status": "ok"}
