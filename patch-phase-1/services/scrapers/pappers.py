"""
Scraper Pappers - Scraping HTTP respectueux
Récupère les données légales des entreprises françaises
Note: Utiliser avec modération (rate limiting strict)
"""
import httpx
from typing import Optional, Dict, Any, List
from .base import BaseScraper, ScraperError


class PappersScraper(BaseScraper):
    """Scraper pour Pappers.fr (scraping HTTP)"""

    BASE_URL = "https://www.pappers.fr/entreprise"
    RATE_LIMIT = 2  # 2 requêtes par seconde maximum
    MAX_RETRIES = 2

    async def search_by_siret(self, siret: str) -> Optional[Dict[str, Any]]:
        """Recherche une entreprise par SIRET sur Pappers"""
        siren = siret[:9] if len(siret) >= 9 else siret
        
        try:
            async with httpx.AsyncClient() as client:
                await self._rate_limit_wait()
                
                # Recherche la page de l'entreprise
                url = f"{self.BASE_URL}/{siren}"
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml"
                    },
                    timeout=self.timeout,
                    follow_redirects=True
                )
                
                if response.status_code == 404:
                    return None
                    
                response.raise_for_status()
                
                # Parsing HTML basique (à améliorer avec BeautifulSoup si nécessaire)
                html = response.text
                return self._parse_html(html, siret)

        except httpx.HTTPError as e:
            raise ScraperError(f"Pappers: Erreur HTTP - {str(e)}")
        except Exception as e:
            raise ScraperError(f"Pappers: Erreur inattendue - {str(e)}")

    async def search_by_siren(self, siren: str) -> Optional[Dict[str, Any]]:
        """Recherche une entreprise par SIREN"""
        return await self.search_by_siret(siren + "00001")

    async def search_by_name(self, name: str, location: Optional[str] = None) -> List:
        """Recherche par nom d'entreprise"""
        # Pappers n'a pas de recherche publique facile à scraper
        # On retourne une liste vide avec un warning
        self.logger.warning("Pappers: Recherche par nom non supportée sans API key")
        return []

    def _parse_html(self, html: str, siret: str) -> Optional[Dict[str, Any]]:
        """Parse le HTML de la page Pappers"""
        # Parsing basique - à améliorer avec BeautifulSoup en production
        try:
            # Extraction simple avec regex (version minimale)
            import re
            
            # Raison sociale
            raison_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
            raison_sociale = raison_match.group(1).strip() if raison_match else None
            
            # SIRET complet
            siret_match = re.search(r'SIRET[:\s]*(\d{14})', html)
            full_siret = siret_match.group(1) if siret_match else siret
            
            # Adresse
            adresse_match = re.search(r'Adresse\s*:\s*([^<]+)', html)
            adresse = adresse_match.group(1).strip() if adresse_match else None
            
            # Activité
            activite_match = re.search(r'Activité\(s\)\s*:\s*([^<]+)', html)
            activite = activite_match.group(1).strip() if activite_match else None
            
            # Date de création
            creation_match = re.search(r'Création\s*:\s*([^<]+)', html)
            date_creation = creation_match.group(1).strip() if creation_match else None
            
            # Capital social
            capital_match = re.search(r'Capital\s*:\s*([\d\s,]+)\s*€', html)
            capital = capital_match.group(1).replace(' ', '').replace(',', '.') if capital_match else None

            return {
                "siret": full_siret,
                "siren": full_siret[:9] if full_siret else siret[:9],
                "raison_sociale": raison_sociale,
                "nom_commercial": None,
                "adresse": adresse,
                "code_postal": None,
                "ville": None,
                "telephone": None,
                "email": None,
                "site_web": None,
                "secteur_activite": activite,
                "code_naf": None,
                "effectif": None,
                "chiffre_affaires": None,
                "date_creation": date_creation,
                "capital_social": capital,
                "source": "pappers"
            }

        except Exception as e:
            self.logger.error(f"Pappers: Erreur lors du parsing HTML - {str(e)}")
            return None

    async def get_documents(self, siren: str) -> List[Dict[str, Any]]:
        """Récupère la liste des documents disponibles"""
        # Version simplifiée - retournerait la liste des statuts, PV, etc.
        self.logger.info(f"Pappers: Récupération documents pour {siren}")
        return []
