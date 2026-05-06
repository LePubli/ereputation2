"""
Scraper INSEE - API publique gratuite
Récupère les données SIRENE des entreprises françaises
Source: https://recherche-entreprises.api.gouv.fr/
"""
import httpx
from typing import Optional, Dict, Any
from .base import BaseScraper, ScraperError


class InseeScraper(BaseScraper):
    """Scraper pour l'API INSEE (recherche-entreprises.api.gouv.fr)"""

    BASE_URL = "https://recherche-entreprises.api.gouv.fr"

    async def search_by_siret(self, siret: str) -> Optional[Dict[str, Any]]:
        """Recherche une entreprise par son SIRET"""
        endpoint = f"{self.BASE_URL}/search"
        params = {"q": siret, "per_page": 1}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    params=params,
                    headers={"User-Agent": self.user_agent},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("total_results", 0) > 0:
                    etablissement = data["results"][0]
                    return self._parse_etablissement(etablissement)
                return None

        except httpx.HTTPError as e:
            raise ScraperError(f"INSEE: Erreur HTTP - {str(e)}")
        except Exception as e:
            raise ScraperError(f"INSEE: Erreur inattendue - {str(e)}")

    async def search_by_siren(self, siren: str) -> Optional[Dict[str, Any]]:
        """Recherche une entreprise par son SIREN"""
        endpoint = f"{self.BASE_URL}/search"
        params = {"q": siren, "per_page": 1, "est_siege": "true"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    params=params,
                    headers={"User-Agent": self.user_agent},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("total_results", 0) > 0:
                    etablissement = data["results"][0]
                    return self._parse_etablissement(etablissement)
                return None

        except httpx.HTTPError as e:
            raise ScraperError(f"INSEE: Erreur HTTP - {str(e)}")
        except Exception as e:
            raise ScraperError(f"INSEE: Erreur inattendue - {str(e)}")

    async def search_by_name(self, name: str, location: Optional[str] = None) -> list:
        """Recherche des entreprises par nom"""
        endpoint = f"{self.BASE_URL}/search"
        params = {"q": name, "per_page": 10}
        if location:
            params["localisation"] = location

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    params=params,
                    headers={"User-Agent": self.user_agent},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for etablissement in data.get("results", []):
                    parsed = self._parse_etablissement(etablissement)
                    if parsed:
                        results.append(parsed)

                return results

        except httpx.HTTPError as e:
            raise ScraperError(f"INSEE: Erreur HTTP - {str(e)}")
        except Exception as e:
            raise ScraperError(f"INSEE: Erreur inattendue - {str(e)}")

    def _parse_etablissement(self, data: Dict) -> Optional[Dict[str, Any]]:
        """Parse les données d'un établissement"""
        try:
            entreprise = data.get("entreprise", {})
            etablissement = data.get("etablissements", [{}])[0] if "etablissements" in data else data

            adresse = etablissement.get("adresse", {})
            dirigeants = entreprise.get("dirigeants", [])

            return {
                "siret": etablissement.get("siret"),
                "siren": entreprise.get("siren"),
                "raison_sociale": entreprise.get("nom_complet") or entreprise.get("raison_sociale"),
                "nom_commercial": entreprise.get("nom_commercial"),
                "adresse": self._format_adresse(adresse),
                "code_postal": adresse.get("code_postal"),
                "ville": adresse.get("commune"),
                "telephone": etablissement.get("telephone"),
                "email": etablissement.get("email"),
                "site_web": etablissement.get("site_internet"),
                "secteur_activite": entreprise.get("libelle_nature_juridique"),
                "code_naf": etablissement.get("activite_principale"),
                "libelle_naf": etablissement.get("libelle_activite_principale"),
                "effectif": etablissement.get("tranche_effectif_salarie"),
                "date_creation": entreprise.get("date_creation"),
                "etat_administratif": entreprise.get("etat_administratif"),
                "dirigeants": self._parse_dirigeants(dirigeants),
                "source": "insee"
            }
        except Exception as e:
            self.logger.warning(f"INSEE: Erreur lors du parsing - {str(e)}")
            return None

    def _format_adresse(self, adresse: Dict) -> str:
        """Formate une adresse complète"""
        parts = []
        if adresse.get("numero_voie"):
            parts.append(f"{adresse.get('numero_voie')} {adresse.get('type_voie', '')} {adresse.get('libelle_voie', '')}")
        if adresse.get("lieu_dit"):
            parts.append(adresse.get("lieu_dit"))
        if adresse.get("code_postal") and adresse.get("commune"):
            parts.append(f"{adresse.get('code_postal')} {adresse.get('commune')}")
        return ", ".join(filter(None, parts))

    def _parse_dirigeants(self, dirigeants: list) -> list:
        """Parse la liste des dirigeants"""
        result = []
        for dirigeant in dirigeants or []:
            result.append({
                "nom": dirigeant.get("nom"),
                "prenom": dirigeant.get("prenoms"),
                "fonction": dirigeant.get("titre"),
                "date_nomination": dirigeant.get("date_naissance")
            })
        return result
