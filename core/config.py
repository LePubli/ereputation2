"""Configuration centralisée Phase finale — ajout Qwen, Groq, Ollama."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # --- Application ---
    APP_NAME: str = "B2B Prospector"
    APP_VERSION: str = "4.0.0"
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
    DATABASE_URL: str = "postgresql+asyncpg://prospector:prospector@db:5432/prospector"
    DATABASE_URL_SYNC: str = "postgresql://prospector:prospector@db:5432/prospector"
    POSTGRES_USER: str = "prospector"
    POSTGRES_PASSWORD: str = "prospector"
    POSTGRES_DB: str = "prospector"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # --- Redis ---
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # --- Plugins ---
    PLUGINS_DIR: str = "/app/plugins"
    PLUGINS_AUTO_DISCOVER: bool = True

    # --- AI Providers (multi-LLM) ---
    # Claude (Anthropic) — RECOMMANDÉ pour web search
    ANTHROPIC_API_KEY: str = ""

    # Qwen (Alibaba) — GRATUIT 1M tokens/mois
    # Inscription : https://dashscope.console.aliyun.com/
    QWEN_API_KEY: str = ""
    QWEN_MODEL: str = "qwen-turbo"  # Options: qwen-turbo, qwen-plus, qwen-max, qwen-long

    # Groq (Llama) — GRATUIT 500k tokens/jour
    # Inscription : https://console.groq.com/
    GROQ_API_KEY: str = ""

    # Ollama (local sur serveur) — 100% GRATUIT
    # Installation : curl -fsSL https://ollama.ai/install.sh | sh && ollama pull mistral
    OLLAMA_URL: str = ""  # ex: http://localhost:11434

    # --- Scrapers ---
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (compatible; B2BProspector/4.0)"
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_RATE_LIMIT_PER_MINUTE: int = 20
    SCRAPER_CACHE_TTL_HOURS: int = 24
    SCRAPER_RETRY_ATTEMPTS: int = 3

    INSEE_RECHERCHE_API: str = "https://recherche-entreprises.api.gouv.fr/search"
    BODACC_API: str = "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records"
    PAPPERS_BASE_URL: str = "https://www.pappers.fr"
    PAGES_JAUNES_BASE_URL: str = "https://www.pagesjaunes.fr"

    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_NAV_TIMEOUT: int = 20000

    # --- Contact Intelligence (APIs payantes optionnelles) ---
    HUNTER_API_KEY: str = ""          # Hunter.io — 50 gratuit/mois
    DROPCONTACT_API_KEY: str = ""     # Dropcontact — RGPD France, ~0.02€/contact
    APOLLO_API_KEY: str = ""          # Apollo.io — 200 gratuit/mois
    SNOVIO_CLIENT_ID: str = ""        # Snov.io — 150 gratuit/mois
    SNOVIO_CLIENT_SECRET: str = ""
    DATAGMA_API_KEY: str = ""         # Mobiles France

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

settings = Settings()
