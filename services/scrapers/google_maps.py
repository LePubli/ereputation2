"""
Scraper Google Maps — Via Playwright headless (anti-détection).

⚠️ AVERTISSEMENT JURIDIQUE :
Le scraping de Google Maps va à l'encontre des CGU Google.
Stratégie : volume très faible, headless avec stealth, mise en cache 24h.
Pour usage commercial à grand volume → API Google Places (1$/1000 requêtes).
Voir docs/SCRAPING_LEGAL.md.

Sortie typique :
- Nom commercial
- Adresse complète
- Téléphone
- Site web
- Note moyenne + nombre d'avis
- Horaires
- Latitude / longitude
"""
import asyncio
from typing import Any
from urllib.parse import quote

from loguru import logger

from core.config import settings
from services.scrapers.base import BaseScraper, ScraperResult


class GoogleMapsScraper(BaseScraper):
    """Scraper Google Maps via Playwright headless."""

    source_name = "google_maps"
    POLITE_DELAY = 2.5
    NAV_TIMEOUT = 20000  # ms

    async def fetch(self, identifier: str) -> ScraperResult:
        """
        identifier : "Nom Entreprise|Ville" ou juste le nom.
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

        query = f"{name} {city}".strip()
        url = f"https://www.google.com/maps/search/{quote(query)}"

        try:
            data = await self._scrape_with_playwright(url, query)
        except Exception as e:
            logger.warning(f"[GoogleMaps] Échec sur {query}: {e}")
            return ScraperResult(self.source_name, success=False, error=str(e))

        if not data:
            return ScraperResult(
                self.source_name,
                success=False,
                error="Aucun résultat trouvé",
            )

        return ScraperResult(self.source_name, success=True, data=data)

    async def _scrape_with_playwright(self, url: str, query: str) -> dict[str, Any] | None:
        """Lance Playwright headless, navigue et extrait les données."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("[GoogleMaps] Playwright non installé. `pip install playwright && playwright install chromium`")
            return None

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )
            context = await browser.new_context(
                user_agent=self._build_headers()["User-Agent"],
                locale="fr-FR",
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

            try:
                await page.goto(url, timeout=self.NAV_TIMEOUT, wait_until="domcontentloaded")
                await asyncio.sleep(self.POLITE_DELAY)

                # Accepter les cookies si présent
                try:
                    accept_btn = await page.query_selector('button[aria-label*="Accepter"], button:has-text("Accept all")')
                    if accept_btn:
                        await accept_btn.click()
                        await asyncio.sleep(1.0)
                except Exception:
                    pass

                # Extraction (best-effort, les sélecteurs Google changent souvent)
                data: dict[str, Any] = {"query": query, "url": url}

                # Nom du lieu
                name_node = await page.query_selector('h1.DUwDvf, h1[class*="fontHeadlineLarge"]')
                if name_node:
                    data["name"] = (await name_node.text_content()) or ""

                # Note + avis
                rating_node = await page.query_selector('div.F7nice span[aria-hidden="true"]')
                if rating_node:
                    rating_text = (await rating_node.text_content()) or ""
                    try:
                        data["rating"] = float(rating_text.replace(",", "."))
                    except ValueError:
                        pass

                reviews_node = await page.query_selector('div.F7nice span[aria-label*="avis"], div.F7nice span[aria-label*="reviews"]')
                if reviews_node:
                    aria = await reviews_node.get_attribute("aria-label") or ""
                    digits = "".join(c for c in aria if c.isdigit())
                    if digits:
                        data["reviews_count"] = int(digits)

                # Adresse, téléphone, site (boutons d'info)
                buttons = await page.query_selector_all('button[data-item-id]')
                for btn in buttons:
                    item_id = await btn.get_attribute("data-item-id") or ""
                    aria = await btn.get_attribute("aria-label") or ""

                    if item_id == "address" or "Adresse" in aria:
                        data["address"] = aria.replace("Adresse: ", "").strip()
                    elif item_id.startswith("phone") or "Téléphone" in aria:
                        data["phone"] = aria.split(":")[-1].strip()
                    elif item_id == "authority" or "Site Web" in aria:
                        href = await btn.get_attribute("data-url") or ""
                        if href:
                            data["website"] = href

                # Coordonnées GPS depuis l'URL après redirection
                current_url = page.url
                if "/@" in current_url:
                    try:
                        coords_part = current_url.split("/@")[1].split(",")
                        data["latitude"] = float(coords_part[0])
                        data["longitude"] = float(coords_part[1])
                    except (IndexError, ValueError):
                        pass

                return data if data.get("name") or data.get("address") else None

            finally:
                await context.close()
                await browser.close()
