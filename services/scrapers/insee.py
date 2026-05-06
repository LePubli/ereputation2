"""
Scraper INSEE — API publique recherche-entreprises.api.gouv.fr

Documentation officielle :
https://api.gouv.fr/documentation/api-recherche-entreprises

Cette API est gérée par data.gouv.fr, ouverte, sans clé requise.
Données : nom légal, SIREN/SIRET, adresse, NAF, dirigeants, effectifs, etc.
"""
from typing import Any

from loguru import logger

from services.scrapers.base import BaseScraper, ScraperResult


class InseeScraper(BaseScraper):
    """Scraper de l'API publique recherche-entreprises (data.gouv.fr)."""

    source_name = "insee"
    BASE_URL = "https://recherche-entreprises.api.gouv.fr"

    async def fetch(self, identifier: str) -> ScraperResult:
        """
        identifier : SIREN (9), SIRET (14) ou texte libre (raison sociale).
        """
        identifier = identifier.replace(" ", "").strip()

        try:
            if identifier.isdigit() and len(identifier) in (9, 14):
                return await self._fetch_by_siren(identifier)
            return await self._fetch_by_text(identifier)
        except Exception as e:
            logger.exception(f"[INSEE] Erreur sur {identifier}")
            return ScraperResult(self.source_name, success=False, error=str(e))

    async def _fetch_by_siren(self, ident: str) -> ScraperResult:
        """Recherche par SIREN/SIRET via le paramètre `q`."""
        siren = ident[:9]
        url = f"{self.BASE_URL}/search"
        try:
            response = await self._http_get(url, params={"q": siren, "page": 1, "per_page": 1})
            data = response.json()
        except Exception as e:
            return ScraperResult(self.source_name, success=False, error=f"HTTP error: {e}")

        results = data.get("results", [])
        if not results:
            return ScraperResult(self.source_name, success=False, error=f"Aucune entreprise trouvée pour {siren}")

        entreprise = results[0]
        return ScraperResult(self.source_name, success=True, data=self._normalize(entreprise))

    async def _fetch_by_text(self, query: str) -> ScraperResult:
        """Recherche libre (raison sociale)."""
        url = f"{self.BASE_URL}/search"
        try:
            response = await self._http_get(url, params={"q": query, "page": 1, "per_page": 5})
            data = response.json()
        except Exception as e:
            return ScraperResult(self.source_name, success=False, error=f"HTTP error: {e}")

        results = data.get("results", [])
        if not results:
            return ScraperResult(self.source_name, success=False, error=f"Aucune entreprise trouvée pour '{query}'")

        return ScraperResult(
            self.source_name,
            success=True,
            data={
                "query": query,
                "matches": [self._normalize(r) for r in results],
                "total": data.get("total_results", len(results)),
            },
        )

    @staticmethod
    def _normalize(e: dict[str, Any]) -> dict[str, Any]:
        """Normalise la réponse INSEE en format applicatif."""
        siege = e.get("siege", {}) or {}
        dirigeants = e.get("dirigeants", []) or []

        return {
            "siren": e.get("siren"),
            "siret": siege.get("siret"),
            "company_name": e.get("nom_complet") or e.get("nom_raison_sociale"),
            "legal_form": e.get("nature_juridique"),
            "naf_code": e.get("activite_principale"),
            "naf_label": e.get("libelle_activite_principale"),
            "creation_date": e.get("date_creation"),
            "employee_range": e.get("tranche_effectif_salarie"),
            "category": e.get("categorie_entreprise"),
            "is_active": e.get("etat_administratif") == "A",
            "address": siege.get("adresse"),
            "postal_code": siege.get("code_postal"),
            "city": siege.get("libelle_commune"),
            "department": siege.get("departement"),
            "region": siege.get("region"),
            "latitude": siege.get("latitude"),
            "longitude": siege.get("longitude"),
            "directors": [
                {
                    "first_name": d.get("prenoms"),
                    "last_name": d.get("nom"),
                    "role": d.get("qualite"),
                }
                for d in dirigeants
            ],
        }
