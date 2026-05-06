"""
Base Scraper - Classe abstraite pour tous les scrapers
Gère: retry, rate limiting, logging, cache
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


class ScraperError(Exception):
    """Exception personnalisée pour les erreurs de scraping"""
    pass


class BaseScraper(ABC):
    """Classe de base pour tous les scrapers"""

    BASE_URL: str = ""
    RATE_LIMIT: int = 10  # requêtes par seconde
    TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0

    def __init__(self, rate_limit: Optional[int] = None, timeout: Optional[int] = None):
        self.rate_limit = rate_limit or self.RATE_LIMIT
        self.timeout = timeout or self.TIMEOUT
        self.logger = logging.getLogger(f"scraper.{self.__class__.__name__}")
        self._last_request: Optional[datetime] = None
        self._request_count: int = 0
        self.user_agent = "Mozilla/5.0 (compatible; B2BProspector/1.0)"

    async def _rate_limit_wait(self):
        """Respecte le rate limiting"""
        if self._last_request:
            elapsed = (datetime.now() - self._last_request).total_seconds()
            min_interval = 1.0 / self.rate_limit
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        self._last_request = datetime.now()
        self._request_count += 1

    async def _retry_request(self, func, *args, **kwargs):
        """Exécute une fonction avec retry exponentiel"""
        last_exception = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    self.logger.warning(
                        f"Tentative {attempt + 1}/{self.MAX_RETRIES} échouée: {str(e)}. "
                        f"Réessai dans {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"Toutes les tentatives échouées: {str(e)}")

        raise ScraperError(f"Échec après {self.MAX_RETRIES} tentatives: {str(last_exception)}")

    @abstractmethod
    async def search_by_siret(self, siret: str) -> Optional[Dict[str, Any]]:
        """Recherche par SIRET - à implémenter par chaque scraper"""
        pass

    @abstractmethod
    async def search_by_siren(self, siren: str) -> Optional[Dict[str, Any]]:
        """Recherche par SIREN - à implémenter par chaque scraper"""
        pass

    @abstractmethod
    async def search_by_name(self, name: str, location: Optional[str] = None) -> List:
        """Recherche par nom - à implémenter par chaque scraper"""
        pass

    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'utilisation du scraper"""
        return {
            "scraper": self.__class__.__name__,
            "request_count": self._request_count,
            "rate_limit": self.rate_limit,
            "last_request": self._last_request.isoformat() if self._last_request else None
        }
