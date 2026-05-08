"""
Scraper Pappers — Scraping HTTP respectueux du site web public.

⚠️ AVERTISSEMENT JURIDIQUE :
Pappers propose une API officielle payante. Le scraping HTML public reste
techniquement possible (les données sont publiques par essence : RNCS) mais
les CGU peuvent évoluer. Voir docs/SCRAPING_LEGAL.md.

Stratégie :
- Rate limit (1 requête / 2 secondes minimum)
- User-Agent identifiant clairement le bot
- Cache 24h en BDD pour réduire la charge
- Recommandation : passer à l'API officielle dès que volume > 100/jour
"""
import asyncio
from typing import Any

from loguru import logger
from selectolax.parser import HTMLParser

from services.scrapers.base import BaseScraper, ScraperResult


class PappersScraper(BaseScraper):
    """Scraper Pappers via les fiches publiques."""

    source_name = "pappers"
    BASE_URL = "https://www.pappers.fr"

    # Délai mini entre 2 requêtes (en secondes)
    POLITE_DELAY = 2.0

    async def fetch(self, identifier: str) -> ScraperResult:
        """identifier : SIREN à 9 chiffres."""
        identifier = identifier.replace(" ", "").strip()
        if not identifier.isdigit() or len(identifier) < 9:
            return ScraperResult(
                self.source_name,
                success=False,
                error="Pappers nécessite un SIREN à 9 chiffres",
            )
        siren = identifier[:9]
        url = f"{self.BASE_URL}/entreprise/{siren}"

        try:
            await asyncio.sleep(self.POLITE_DELAY)
            response = await self._http_get(url)
            # 403 = bloqué par Pappers (volume trop élevé ou IP bloquée)
            if response.status_code in (403, 429):
                logger.warning(f"[Pappers] Bloqué ({response.status_code}) sur {siren}")
                return ScraperResult(self.source_name, success=False, error=f"HTTP {response.status_code}")
            html = response.text
        except Exception as e:
            logger.warning(f"[Pappers] Échec sur {siren}: {e}")
            return ScraperResult(self.source_name, success=False, error=str(e))

        try:
            data = self._parse_html(html, siren)
        except Exception as e:
            logger.exception(f"[Pappers] Parse error sur {siren}")
            return ScraperResult(self.source_name, success=False, error=f"Parse error: {e}")

        return ScraperResult(self.source_name, success=True, data=data)

    @staticmethod
    def _parse_html(html: str, siren: str) -> dict[str, Any]:
        """Extrait les infos clés d'une fiche Pappers."""
        tree = HTMLParser(html)

        def safe_text(selector: str) -> str | None:
            node = tree.css_first(selector)
            return node.text(strip=True) if node else None

        # Données structurées (JSON-LD)
        ld_data = {}
        for ld_node in tree.css('script[type="application/ld+json"]'):
            try:
                import json
                content = ld_node.text() or ""
                parsed = json.loads(content)
                if isinstance(parsed, dict) and parsed.get("@type") in ("Organization", "Corporation", "LocalBusiness"):
                    ld_data = parsed
                    break
            except Exception:
                continue

        company_name = (
            ld_data.get("name")
            or safe_text("h1")
            or safe_text(".company-name")
        )

        # Liens utiles (réseaux sociaux, site web)
        website = None
        for link in tree.css("a[href]"):
            href = link.attributes.get("href", "")
            if href and ("http" in href) and ("pappers.fr" not in href) and ("societe.com" not in href):
                rel = (link.attributes.get("rel") or "").lower()
                if "nofollow" in rel or "external" in rel:
                    website = href
                    break

        # Effectifs / CA depuis le texte (best-effort)
        text = tree.body.text(strip=True) if tree.body else ""

        return {
            "siren": siren,
            "url": f"https://www.pappers.fr/entreprise/{siren}",
            "company_name": company_name,
            "website": website,
            "raw_text_length": len(text),
            "json_ld": ld_data,
        }
