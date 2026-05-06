"""
Scraper BODACC - API publique gratuite
Récupère les mentions légales (créations, radiations, procédures collectives)
Source: https://bodacc-datadila.opendatasoft.com/
"""
import httpx
from typing import Optional, Dict, Any, List
from .base import BaseScraper, ScraperError


class BodaccScraper(BaseScraper):
    """Scraper pour l'API BODACC (opendatasoft)"""

    BASE_URL = "https://bodacc-datadila.opendatasoft.com/api/records/1.0/search"

    async def search_by_siren(self, siren: str) -> List[Dict[str, Any]]:
        """Recherche les mentions BODACC par SIREN"""
        params = {
            "q": f"siren:{siren}",
            "rows": 50,
            "facet": ["typologie"]
        }

        try:
            async with httpx.AsyncClient() as client:
                await self._rate_limit_wait()
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for record in data.get("records", []):
                    fields = record.get("fields", {})
                    results.append({
                        "numero_annonce": fields.get("numero_annonce"),
                        "date_parution": fields.get("date_parution"),
                        "typologie": fields.get("typologie"),
                        "nature_commerce": fields.get("nature_commerce"),
                        "date_effet": fields.get("date_effet"),
                        "raison_sociale": fields.get("denomination"),
                        "siren": fields.get("siren"),
                        "capital": fields.get("capital"),
                        "adresse": fields.get("adresse"),
                        "activite": fields.get("activite"),
                        "url_annonce": fields.get("lien"),
                        "source": "bodacc"
                    })

                return results

        except httpx.HTTPError as e:
            raise ScraperError(f"BODACC: Erreur HTTP - {str(e)}")
        except Exception as e:
            raise ScraperError(f"BODACC: Erreur inattendue - {str(e)}")

    async def search_by_name(self, name: str, location: Optional[str] = None) -> List:
        """Recherche par nom d'entreprise"""
        query = f"denomination:{name}"
        if location:
            query += f" AND departement:{location}"

        params = {
            "q": query,
            "rows": 20,
            "sort": "-date_parution"
        }

        try:
            async with httpx.AsyncClient() as client:
                await self._rate_limit_wait()
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for record in data.get("records", []):
                    fields = record.get("fields", {})
                    results.append({
                        "numero_annonce": fields.get("numero_annonce"),
                        "date_parution": fields.get("date_parution"),
                        "typologie": fields.get("typologie"),
                        "raison_sociale": fields.get("denomination"),
                        "siren": fields.get("siren"),
                        "source": "bodacc"
                    })

                return results

        except httpx.HTTPError as e:
            raise ScraperError(f"BODACC: Erreur HTTP - {str(e)}")
        except Exception as e:
            raise ScraperError(f"BODACC: Erreur inattendue - {str(e)}")

    async def get_recent_mentions(self, days: int = 30) -> List[Dict[str, Any]]:
        """Récupère les mentions récentes (derniers X jours)"""
        # L'API BODACC ne permet pas de filtrer par date directement
        # On retourne les derniers résultats triés
        params = {
            "rows": 100,
            "sort": "-date_parution"
        }

        try:
            async with httpx.AsyncClient() as client:
                await self._rate_limit_wait()
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for record in data.get("records", [])[:days]:
                    fields = record.get("fields", {})
                    results.append({
                        "numero_annonce": fields.get("numero_annonce"),
                        "date_parution": fields.get("date_parution"),
                        "typologie": fields.get("typologie"),
                        "raison_sociale": fields.get("denomination"),
                        "siren": fields.get("siren"),
                        "source": "bodacc"
                    })

                return results

        except httpx.HTTPError as e:
            raise ScraperError(f"BODACC: Erreur HTTP - {str(e)}")
        except Exception as e:
            raise ScraperError(f"BODACC: Erreur inattendue - {str(e)}")

    async def search_by_siret(self, siret: str) -> Optional[Dict[str, Any]]:
        """Recherche par SIRET (dérive vers SIREN)"""
        siren = siret[:9] if len(siret) >= 9 else siret
        results = await self.search_by_siren(siren)
        return results[0] if results else None
