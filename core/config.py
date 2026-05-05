"""
Configuration centrale de l'application B2B Prospector
Gère les variables d'environnement, settings et constantes globales
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from loguru import logger


class Settings(BaseSettings):
    """Configuration globale de l'application"""
    
    # Application
    APP_NAME: str = "B2B Prospector"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # API
    API_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Database (SQLite pour MVP, PostgreSQL en prod)
    DATABASE_URL: str = "sqlite:///./data/prospector.db"
    DATABASE_POOL_SIZE: int = 10
    
    # Redis (Event Bus)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Plugins
    PLUGINS_DIR: Path = Path(__file__).parent.parent / "plugins"
    ACTIVE_PLUGINS: List[str] = [
        "scraper-insee",
        "audit-digital",
        "pain-point-engine",
        "pipeline-kanban"
    ]
    
    # External APIs
    INSEE_API_KEY: Optional[str] = None
    INSEE_API_SECRET: Optional[str] = None
    PAPPERS_API_KEY: Optional[str] = None
    
    # LLM (optionnel, pour formatting uniquement)
    LLM_PROVIDER: str = "ollama"  # ollama, openai, anthropic
    LLM_MODEL: str = "llama3.1:8b"
    LLM_API_URL: str = "http://localhost:11434"
    LLM_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: str = "*"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # RGPD
    DATA_RETENTION_DAYS: int = 365
    ALLOW_B2B_ONLY: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/prospector.log"
    LOG_ROTATION: str = "10 MB"
    LOG_RETENTION: str = "7 days"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instance globale des settings
settings = Settings()


def setup_logging():
    """Configure le logging structuré avec Loguru"""
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configuration Loguru
    logger.remove()  # Retire le handler par défaut
    
    # Console handler
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # File handler
    logger.add(
        log_path,
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        serialize=False
    )
    
    logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}")
    return logger


def get_settings() -> Settings:
    """Retourne l'instance des settings"""
    return settings
