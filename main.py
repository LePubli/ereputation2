"""
Point d'entrée FastAPI — B2B Prospector.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from core.config import settings
from core.database import close_db, init_db
from core.plugin_loader import PluginGateMiddleware, load_plugins


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} — démarrage")
    try:
        await init_db()
        logger.success("✓ Base de données connectée")
    except Exception as e:
        logger.error(f"✗ DB non disponible : {e}")

    loaded = await load_plugins(app)
    active = [k for k, v in loaded.items() if v]
    logger.info(f"📦 Plugins actifs : {', '.join(active) or 'aucun'}")

    yield

    logger.info("👋 Arrêt de l'application")
    await close_db()


# ─────────────────────────────────────────── Middleware Gate (DOIT ÊTRE AJOUTÉ EN PREMIER)
# Ce middleware bloque les routes des plugins inactifs
# Il doit être ajouté AVANT que l'application ne démarre (pas dans lifespan)
from starlette.middleware import Middleware as StarletteMiddleware
_app_middlewares = [
    StarletteMiddleware(PluginGateMiddleware),
]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
    middleware=_app_middlewares,
)

# ─────────────────────────────────────────── CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────── Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# ─────────────────────────────────────────── Rate limiting (simple in-memory)
from collections import defaultdict
from time import time

_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 200        # max requêtes
RATE_WINDOW = 60        # par minute
RATE_LIMIT_AUTH = 10    # tentatives login
RATE_WINDOW_AUTH = 60


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip health + static
    path = request.url.path
    if path in ("/health", "/") or path.startswith("/static"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time()

    # Rate limit plus strict sur auth
    is_auth = "/auth/login" in path or "/auth/refresh" in path
    limit = RATE_LIMIT_AUTH if is_auth else RATE_LIMIT
    window = RATE_WINDOW_AUTH if is_auth else RATE_WINDOW

    key = f"{client_ip}:{path if is_auth else 'global'}"
    timestamps = _rate_limit_store[key]

    # Purge anciens
    _rate_limit_store[key] = [t for t in timestamps if now - t < window]

    if len(_rate_limit_store[key]) >= limit:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Trop de requêtes. Réessayez dans une minute."},
            headers={"Retry-After": str(window)},
        )

    _rate_limit_store[key].append(now)
    return await call_next(request)


# ─────────────────────────────────────────── WebSocket
from plugins.notifications.ws_routes import router as ws_router
app.include_router(ws_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "health": "/health",
    }


@app.get("/health")
async def root_health():
    return {"status": "ok"}
