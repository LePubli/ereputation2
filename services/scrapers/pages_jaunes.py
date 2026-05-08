"""
Scraper Pages Jaunes — Récupération coordonnées entreprises.

⚠️ AVERTISSEMENT JURIDIQUE :
Le scraping de Pages Jaunes est dans une zone grise (CGU restrictives).
Stratégie : volume très faible, User-Agent identifiant, délais respectueux.
Voir docs/SCRAPING_LEGAL.md.
"""
import asyncio
from typing import Any
from urllib.parse import quote_plus

from loguru import logger
from selectolax.parser import HTMLParser

from services.scrapers.base import BaseScraper, ScraperResult


class PagesJaunesScraper(BaseScraper):
    """Scraper Pages Jaunes (annuaire pro)."""

    source_name = "pages_jaunes"
    BASE_URL = "https://www.pagesjaunes.fr"
    POLITE_DELAY = 3.0

    async def fetch(self, identifier: str) -> ScraperResult:
        """
        identifier : "Nom Entreprise|Ville" ou juste le nom.
        Exemples :
            "Laser And Co|Roubaix"
            "Boulanger|Lille"
        """
        if "|" in identifier:
            name, city = identifier.split("|", 1)
        else:
            name, city = identifier, ""

        name = name.strip()
        city = city.strip()

        if not name:
            return ScraperResult(
                self.source_name,
                success=False,
                error="Nom d'entreprise requis",
            )

        url = f"{self.BASE_URL}/annuaire/chercherlespros"
        params = {"quoiqui": name}
        if city:
            params["ou"] = city

        try:
            await asyncio.sleep(self.POLITE_DELAY)
            response = await self._http_get(url, params=params)
            if response.status_code in (403, 429):
                logger.warning(f"[PagesJaunes] Bloqué ({response.status_code}) sur {name}/{city}")
                return ScraperResult(self.source_name, success=False, error=f"HTTP {response.status_code}")
            html = response.text
        except Exception as e:
            logger.warning(f"[PagesJaunes] Échec sur {name}/{city}: {e}")
            return ScraperResult(self.source_name, success=False, error=str(e))

        try:
            data = self._parse_search_results(html, name, city)
        except Exception as e:
            logger.exception(f"[PagesJaunes] Parse error")
            return ScraperResult(self.source_name, success=False, error=f"Parse error: {e}")

        return ScraperResult(self.source_name, success=True, data=data)

    @staticmethod
    def _parse_search_results(html: str, name: str, city: str) -> dict[str, Any]:
        """Extrait les premiers résultats de recherche."""
        tree = HTMLParser(html)
        results = []

        # Sélecteurs adaptables (PJ change régulièrement)
        cards = tree.css("article.bi") or tree.css("li.bi") or tree.css(".bi-content")

        for card in cards[:10]:
            name_node = card.css_first("a.denomination-links, h3 a, .denomination a")
            phone_node = card.css_first(".coord-numero, .num-tel, [class*='phone']")
            address_node = card.css_first(".address, .adresse, [class*='adresse']")

            entry = {
                "name": name_node.text(strip=True) if name_node else None,
                "phone": phone_node.text(strip=True) if phone_node else None,
                "address": address_node.text(strip=True) if address_node else None,
            }
            if entry["name"]:
                results.append(entry)

        return {
            "query": {"name": name, "city": city},
            "results": results,
            "count": len(results),
            "search_url": f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui={quote_plus(name)}&ou={quote_plus(city)}",
        }
