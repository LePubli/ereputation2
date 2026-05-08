"""
Scraper BODACC — API publique data.gouv.fr (Opendatasoft)

URL : https://bodacc-datadila.opendatasoft.com/explore/dataset/annonces-commerciales/

Cette API est ouverte, sans clé. Elle retourne les annonces officielles BODACC
(Bulletin Officiel des Annonces Civiles et Commerciales) :
- Créations d'entreprise
- Procédures collectives
- Cessions, dépôts de comptes
- Modifications statutaires
"""
from loguru import logger

from services.scrapers.base import BaseScraper, ScraperResult


class BodaccScraper(BaseScraper):
    """Scraper de l'API BODACC (Opendatasoft / data.gouv.fr)."""

    source_name = "bodacc"
    BASE_URL = "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records"

    async def fetch(self, identifier: str) -> ScraperResult:
        """identifier : SIREN (9 chiffres) — on filtre sur registre.siren."""
        identifier = identifier.replace(" ", "").strip()

        if not identifier.isdigit() or len(identifier) < 9:
            return ScraperResult(
                self.source_name,
                success=False,
                error="BODACC nécessite un SIREN à 9 chiffres",
            )
        siren = identifier[:9]

        try:
            # Guillemets SIMPLES obligatoires pour la syntaxe ODSQL
            params = {
                "where": f"registre LIKE '{siren}%' OR rcs LIKE '{siren}%'",
                "limit": 20,
                "order_by": "dateparution desc",
            }
            response = await self._http_get(self.BASE_URL, params=params)
            data = response.json()
        except Exception as e:
            logger.warning(f"[BODACC] Échec sur {siren}: {e}")
            return ScraperResult(self.source_name, success=False, error=str(e))

        records = data.get("results", []) or []
        annonces = [self._normalize(r) for r in records]

        # Détection signaux faibles
        has_collective = any(
            "procedure" in (a.get("category") or "").lower()
            or "redressement" in (a.get("category") or "").lower()
            or "liquidation" in (a.get("category") or "").lower()
            for a in annonces
        )

        return ScraperResult(
            self.source_name,
            success=True,
            data={
                "siren": siren,
                "annonces": annonces,
                "count": len(annonces),
                "has_collective_procedure": has_collective,
                "last_publication": annonces[0]["date_parution"] if annonces else None,
            },
        )

    @staticmethod
    def _normalize(rec: dict) -> dict:
        return {
            "id": rec.get("id"),
            "date_parution": rec.get("dateparution"),
            "category": rec.get("familleavis_lib") or rec.get("typeavis_lib"),
            "departement": rec.get("departement_nom_officiel"),
            "tribunal": rec.get("tribunal"),
            "registre": rec.get("registre"),
            "publication_avis": rec.get("publicationavis"),
            "type_annonce": rec.get("typeavis_lib"),
        }
