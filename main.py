"""
B2B Prospector - Application principale FastAPI
Copilote commercial B2B modulaire et production-ready
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from core.config import settings, setup_logging
from core.event_bus import event_bus
from core.plugin_manager import plugin_manager


# Configuration du logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Gestion du cycle de vie de l'application"""
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Connect to EventBus
    await event_bus.connect()
    
    # Discover and load plugins
    discovered = plugin_manager.discover()
    logger.info(f"Discovered plugins: {discovered}")
    
    # Initialize active plugins
    loaded = plugin_manager.initialize_all()
    logger.info(f"Loaded {loaded} plugins")
    
    # Start event listener in background
    asyncio.create_task(event_bus.listen())
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await event_bus.disconnect()


# Création de l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Copilote commercial B2B intelligent et modulaire",
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de logging des requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )


# Routes de santé
@app.get("/health")
async def health_check():
    """Endpoint de santé de l'application"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "plugins_active": plugin_manager.get_active()
    }


@app.get("/ready")
async def readiness_check():
    """Endpoint de readiness pour Kubernetes"""
    return {"status": "ready"}


# Route racine
@app.get("/")
async def root():
    """Page d'accueil avec informations de l'API"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Copilote commercial B2B intelligent",
        "docs_url": "/docs",
        "plugins": plugin_manager.get_active(),
        "endpoints_count": len(plugin_manager.get_all_endpoints())
    }


# Endpoint pour lister tous les endpoints des plugins
@app.get("/api/v1/endpoints")
async def list_endpoints():
    """Liste tous les endpoints disponibles des plugins"""
    return {
        "endpoints": plugin_manager.get_all_endpoints(),
        "count": len(plugin_manager.get_all_endpoints())
    }


# Gestion des plugins via API
@app.get("/api/v1/plugins")
async def list_plugins():
    """Liste tous les plugins découverts"""
    plugins = []
    for name, info in plugin_manager.plugins.items():
        plugins.append({
            "name": info.name,
            "version": info.version,
            "description": info.description,
            "active": info.active,
            "dependencies": info.dependencies,
            "endpoints": info.endpoints
        })
    
    return {
        "plugins": plugins,
        "active_count": len(plugin_manager.get_active()),
        "inactive_count": len(plugin_manager.get_inactive())
    }


@app.post("/api/v1/plugins/{plugin_name}/enable")
async def enable_plugin(plugin_name: str):
    """Active un plugin"""
    if plugin_name not in plugin_manager.plugins:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")
    
    success = plugin_manager.enable(plugin_name)
    
    if success:
        return {"success": True, "message": f"Plugin {plugin_name} enabled"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to enable plugin {plugin_name}")


@app.post("/api/v1/plugins/{plugin_name}/disable")
async def disable_plugin(plugin_name: str):
    """Désactive un plugin"""
    if plugin_name not in plugin_manager.plugins:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")
    
    success = plugin_manager.disable(plugin_name)
    
    if success:
        return {"success": True, "message": f"Plugin {plugin_name} disabled"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to disable plugin {plugin_name}")


# Router dynamique pour les endpoints des plugins
# Note: Dans une implémentation complète, il faudrait un système de routing plus sophistiqué
# qui mappe les endpoints définis dans les manifest.yaml vers les handlers des plugins


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
