"""
Configuration centralisée — chargée depuis .env.

Usage :
    from core.config import settings
    settings.DATABASE_URL  # ...
"""
import sys
from pathlib import Path

from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables d'environnement de l'application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "B2B Prospector"
    APP_VERSION: str = "1.1.0"
    APP_ENV: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # --- API ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # --- Sécurité ---
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # --- CORS ---
    CORS_ORIGINS: str = "https://prospect.le-publicitaire.fr,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # --- DB ---
    POSTGRES_USER: str = "prospector"
    POSTGRES_PASSWORD: str = "prospector"
    POSTGRES_DB: str = "prospector"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://prospector:prospector@db:5432/prospector"
    DATABASE_URL_SYNC: str = "postgresql://prospector:prospector@db:5432/prospector"

    # --- Redis ---
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://redis:6379/0"
    EVENT_BUS_CHANNEL: str = "prospector.events"
    EVENT_BUS_CONNECT_TIMEOUT: float = 5.0

    # --- Plugins ---
    PLUGINS_DIR: Path = Path("plugins")
    PLUGINS_AUTO_DISCOVER: bool = True
    ACTIVE_PLUGINS: str = ""

    @property
    def active_plugins_list(self) -> list[str]:
        """Return active plugins from comma-separated env configuration."""
        return [p.strip() for p in self.ACTIVE_PLUGINS.split(",") if p.strip()]

    # --- Scrapers ---
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (compatible; B2BProspector/1.1)"
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_RATE_LIMIT_PER_MINUTE: int = 20
    SCRAPER_CACHE_TTL_HOURS: int = 24
    SCRAPER_RETRY_ATTEMPTS: int = 3

    INSEE_API_KEY: str = ""
    INSEE_API_SECRET: str = ""
    PAPPERS_API_KEY: str = ""
    INSEE_RECHERCHE_API: str = "https://recherche-entreprises.api.gouv.fr/search"
    BODACC_API: str = "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records"
    PAPPERS_BASE_URL: str = "https://www.pappers.fr"
    PAGES_JAUNES_BASE_URL: str = "https://www.pagesjaunes.fr"
    GOOGLE_MAPS_BASE_URL: str = "https://www.google.com/maps"

    # --- Playwright ---
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_NAV_TIMEOUT: int = 20000

    # --- SMTP PlanetHoster ---
    SMTP_HOST: str = "mail.le-publicitaire.fr"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@le-publicitaire.fr"
    SMTP_FROM_NAME: str = "B2B Prospector"
    SMTP_USE_TLS: bool = True

    # --- Admin ---
    ADMIN_EMAIL: str = "admin@le-publicitaire.fr"
    ADMIN_PASSWORD: str = "Admin1234!"
    ADMIN_FULL_NAME: str = "Administrateur"

    # --- Sentry ---
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "production"


settings = Settings()


def setup_logging() -> None:
    """Configure Loguru for container-friendly stdout and optional file logs."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        colorize=False,
        backtrace=settings.DEBUG,
        diagnose=settings.DEBUG,
    )

    log_dir = Path("/app/logs")
    if log_dir.exists() and log_dir.is_dir():
        try:
            logger.add(
                log_dir / "app.log",
                level=settings.LOG_LEVEL,
                rotation="10 MB",
                retention="14 days",
                compression="gz",
                backtrace=settings.DEBUG,
                diagnose=settings.DEBUG,
            )
        except Exception as exc:
            logger.warning(f"File logging disabled: {exc}")

