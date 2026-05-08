"""
Classe de base pour tous les scrapers.

Fournit :
- Client httpx async réutilisable
- Retry exponentiel (tenacity)
- Rate limiting par scraper
- Cache en BDD via ScrapeCache
- User-Agent rotatif (fake-useragent)
"""
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fake_useragent import UserAgent
from loguru import logger
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.config import settings


class ScraperResult:
    """Résultat d'un scraping. Standardisé pour tous les scrapers."""

    def __init__(
        self,
        source: str,
        success: bool,
        data: dict[str, Any] | None = None,
        error: str | None = None,
        from_cache: bool = False,
    ):
        self.source = source
        self.success = success
        self.data = data or {}
        self.error = error
        self.from_cache = from_cache
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "from_cache": self.from_cache,
            "timestamp": self.timestamp,
        }

    def __bool__(self) -> bool:
        return self.success


class BaseScraper(ABC):
    """Classe abstraite pour tous les scrapers."""

    source_name: str = "base"

    def __init__(self):
        self._ua = UserAgent(fallback="Mozilla/5.0 (compatible; B2BProspector/1.1)")
        self._semaphore = asyncio.Semaphore(5)  # max 5 requêtes parallèles
        self.timeout = settings.SCRAPER_TIMEOUT
        self.retry_attempts = settings.SCRAPER_RETRY_ATTEMPTS

    def _build_headers(self) -> dict[str, str]:
        """Headers HTTP avec User-Agent rotatif."""
        try:
            ua = self._ua.random
        except Exception:
            ua = settings.SCRAPER_USER_AGENT
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def _http_get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """GET avec retry exponentiel et timeout."""
        headers = self._build_headers()
        if extra_headers:
            headers.update(extra_headers)

        async with self._semaphore:
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self.retry_attempts),
                    wait=wait_exponential(multiplier=1, min=1, max=10),
                    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)),
                    reraise=True,
                ):
                    with attempt:
                        async with httpx.AsyncClient(
                            timeout=self.timeout,
                            follow_redirects=True,
                            http2=False,
                        ) as client:
                            response = await client.get(url, params=params, headers=headers)
                            # Ne retry que les 5xx, les 4xx (403/400) sont retournés
                            if response.status_code >= 500:
                                response.raise_for_status()
                            return response
            except RetryError as e:
                logger.warning(f"[{self.source_name}] Retry exhausted on {url}: {e}")
                raise

    @abstractmethod
    async def fetch(self, identifier: str) -> ScraperResult:
        """
        Récupère les données pour un identifiant donné.

        identifier dépend du scraper :
            - INSEE/BODACC/Pappers : SIREN ou SIRET
            - Pages Jaunes/Google Maps : nom + ville
        """
        ...

    @staticmethod
    def cache_ttl() -> timedelta:
        """Durée de vie du cache pour cette source."""
        return timedelta(hours=settings.SCRAPER_CACHE_TTL_HOURS)
