"""
Scraper Pages Jaunes - Scraping HTTP respectueux
Récupère les coordonnées et avis des entreprises
Note: Utiliser avec modération (rate limiting strict, delays)
"""
import httpx
from typing import Optional, Dict, Any, List
from .base import BaseScraper, ScraperError


class PagesJaunesScraper(BaseScraper):
    """Scraper pour PagesJaunes.fr (scraping HTTP)"""

    BASE_URL = "https://www.pagesjaunes.fr"
    SEARCH_URL = "https://www.pagesjaunes.fr/pagesblanches/recherche"
    RATE_LIMIT = 1  # 1 requête par seconde maximum
    DELAY_BETWEEN_REQUESTS = 3  # 3 secondes entre chaque requête
    MAX_RETRIES = 2

    async def search_by_name(self, name: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recherche une entreprise par nom et localisation"""
        params = {
            "quoiqui": name,
            "où": location or "France"
        }

        try:
            async with httpx.AsyncClient() as client:
                await self._rate_limit_wait()
                
                response = await client.get(
                    self.SEARCH_URL,
                    params=params,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "fr-FR,fr;q=0.9"
                    },
                    timeout=self.timeout,
                    follow_redirects=True
                )
                
                if response.status_code == 404:
                    return []
                    
                response.raise_for_status()
                html = response.text
                
                return self._parse_search_results(html)

        except httpx.HTTPError as e:
            raise ScraperError(f"PagesJaunes: Erreur HTTP - {str(e)}")
        except Exception as e:
            raise ScraperError(f"PagesJaunes: Erreur inattendue - {str(e)}")

    async def search_by_siret(self, siret: str) -> Optional[Dict[str, Any]]:
        """Recherche par SIRET (non supporté directement, fallback sur nom)"""
        self.logger.warning("PagesJaunes: Recherche par SIRET non supportée")
        return None

    async def search_by_siren(self, siren: str) -> Optional[Dict[str, Any]]:
        """Recherche par SIREN (non supporté directement)"""
        self.logger.warning("PagesJaunes: Recherche par SIREN non supportée")
        return None

    def _parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        """Parse les résultats de recherche HTML"""
        # Parsing basique - à améliorer avec BeautifulSoup en production
        try:
            import re
            
            results = []
            
            # Extraction des cartes d'entreprises (pattern simplifié)
            # En production, utiliser BeautifulSoup pour un parsing robuste
            cards = re.findall(
                r'<article[^>]*>.*?</article>',
                html,
                re.DOTALL | re.IGNORECASE
            )
            
            for card in cards[:10]:  # Limiter à 10 résultats
                # Nom de l'entreprise
                nom_match = re.search(r'denomination[^>]*>([^<]+)', card, re.IGNORECASE)
                nom = nom_match.group(1).strip() if nom_match else None
                
                # Adresse
                adresse_match = re.search(r'<address[^>]*>([^<]+)', card, re.IGNORECASE)
                adresse = adresse_match.group(1).strip() if adresse_match else None
                
                # Téléphone
                tel_match = re.search(r'tel:[\+\d\s]+', card, re.IGNORECASE)
                telephone = tel_match.group(0).replace('tel:', '').strip() if tel_match else None
                
                if nom:
                    results.append({
                        "nom": nom,
                        "adresse": adresse,
                        "telephone": telephone,
                        "email": None,
                        "site_web": None,
                        "horaires": None,
                        "avis": None,
                        "note": None,
                        "source": "pagesjaunes"
                    })

            return results

        except Exception as e:
            self.logger.error(f"PagesJaunes: Erreur lors du parsing HTML - {str(e)}")
            return []

    async def get_details(self, url_fiche: str) -> Optional[Dict[str, Any]]:
        """Récupère les détails d'une fiche entreprise"""
        try:
            async with httpx.AsyncClient() as client:
                await self._rate_limit_wait()
                
                full_url = url_fiche if url_fiche.startswith('http') else f"{self.BASE_URL}{url_fiche}"
                response = await client.get(
                    full_url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml"
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                return self._parse_details_page(response.text)

        except Exception as e:
            self.logger.error(f"PagesJaunes: Erreur récupération détails - {str(e)}")
            return None

    def _parse_details_page(self, html: str) -> Dict[str, Any]:
        """Parse la page de détails d'une entreprise"""
        # À implémenter avec BeautifulSoup en production
        return {}

    async def search_coordinates(self, latitude: float, longitude: float, radius: int = 1000) -> List:
        """Recherche les entreprises autour de coordonnées GPS"""
        # PagesJaunes n'a pas d'API coords facile à scraper
        self.logger.warning("PagesJaunes: Recherche par coordonnées non supportée")
        return []
