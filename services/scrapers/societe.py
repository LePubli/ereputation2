"""
Scraper Société.com — données financières publiques.

Données extraites : CA, résultat net, effectifs, dirigeants.
"""
import asyncio
from typing import Any
from loguru import logger
from selectolax.parser import HTMLParser
from services.scrapers.base import BaseScraper, ScraperResult


class SocieteScraper(BaseScraper):
    source_name = "societe_com"
    BASE_URL = "https://www.societe.com/cgi-bin/search"
    POLITE_DELAY = 2.5

    async def fetch(self, identifier: str) -> ScraperResult:
        identifier = identifier.replace(" ", "").strip()
        if not identifier.isdigit() or len(identifier) < 9:
            return ScraperResult(self.source_name, success=False, error="SIREN requis")
        siren = identifier[:9]

        url = f"https://www.societe.com/societe/x-{siren}.html"
        try:
            await asyncio.sleep(self.POLITE_DELAY)
            response = await self._http_get(url)
            if response.status_code in (403, 429, 404):
                return ScraperResult(self.source_name, success=False, error=f"HTTP {response.status_code}")
            return ScraperResult(self.source_name, success=True, data=self._parse(response.text, siren))
        except Exception as e:
            logger.warning(f"[Societe.com] Échec {siren}: {e}")
            return ScraperResult(self.source_name, success=False, error=str(e))

    @staticmethod
    def _parse(html: str, siren: str) -> dict[str, Any]:
        tree = HTMLParser(html)
        data: dict[str, Any] = {"siren": siren, "url": f"https://www.societe.com/societe/x-{siren}.html"}

        # Chiffre d'affaires
        for node in tree.css(".chiffre, .ca, [class*='turnover'], [class*='revenue']"):
            text = node.text(strip=True)
            if "€" in text or "EUR" in text:
                import re
                nums = re.findall(r'[\d\s]+', text.replace('\xa0', ''))
                if nums:
                    data["revenue_text"] = text.strip()
                break

        # Dirigeants
        directors = []
        for node in tree.css(".dirigeant, [class*='manager'], [class*='director']"):
            name = node.text(strip=True)
            if name and len(name) > 3:
                directors.append(name)
        if directors:
            data["directors_names"] = directors[:5]

        return data
