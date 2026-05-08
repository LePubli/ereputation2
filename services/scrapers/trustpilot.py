"""Scraper Trustpilot — note + avis publics."""
import asyncio
from typing import Any
from loguru import logger
from selectolax.parser import HTMLParser
from urllib.parse import quote_plus
from services.scrapers.base import BaseScraper, ScraperResult


class TrustpilotScraper(BaseScraper):
    source_name = "trustpilot"
    BASE_URL = "https://www.trustpilot.com/search"
    POLITE_DELAY = 2.0

    async def fetch(self, identifier: str) -> ScraperResult:
        """identifier : domaine ou nom de l'entreprise."""
        if "|" in identifier:
            name, _ = identifier.split("|", 1)
        else:
            name = identifier

        name = name.strip()
        try:
            await asyncio.sleep(self.POLITE_DELAY)
            params = {"query": name}
            response = await self._http_get(self.BASE_URL, params=params)
            if response.status_code in (403, 429):
                return ScraperResult(self.source_name, success=False, error=f"HTTP {response.status_code}")
            data = self._parse_search(response.text, name)
            return ScraperResult(self.source_name, success=bool(data.get("rating")), data=data)
        except Exception as e:
            logger.warning(f"[Trustpilot] Échec {name}: {e}")
            return ScraperResult(self.source_name, success=False, error=str(e))

    @staticmethod
    def _parse_search(html: str, query: str) -> dict[str, Any]:
        tree = HTMLParser(html)
        data: dict[str, Any] = {"query": query}

        # Premier résultat
        first = tree.css_first("[class*='businessUnitResult'], [data-business-unit]")
        if not first:
            return data

        rating_node = first.css_first("[class*='trustScore'], [class*='rating']")
        if rating_node:
            text = rating_node.text(strip=True)
            try:
                data["rating"] = float(text.replace(",", "."))
            except ValueError:
                pass

        reviews_node = first.css_first("[class*='reviewCount'], [class*='review-count']")
        if reviews_node:
            import re
            nums = re.findall(r'\d+', reviews_node.text(strip=True).replace('\xa0', '').replace(' ', ''))
            if nums:
                data["reviews_count"] = int("".join(nums))

        name_node = first.css_first("[class*='businessName'], h2, h3")
        if name_node:
            data["company_name"] = name_node.text(strip=True)

        return data
