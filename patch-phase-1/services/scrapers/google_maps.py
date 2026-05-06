"""
Scraper Google Maps - Playwright headless
Récupère les fiches Google Business des entreprises
Note: Utiliser avec modération, delays importants, et rotation User-Agent
"""
import asyncio
from typing import Optional, Dict, Any, List
from .base import BaseScraper, ScraperError


class GoogleMapsScraper(BaseScraper):
    """Scraper pour Google Maps via Playwright"""

    BASE_URL = "https://www.google.com/maps"
    RATE_LIMIT = 1  # 1 requête toutes les 5 secondes minimum
    DELAY_BETWEEN_REQUESTS = 5
    MAX_RETRIES = 2

    def __init__(self, rate_limit: Optional[int] = None, timeout: Optional[int] = None, headless: bool = True):
        super().__init__(rate_limit, timeout)
        self.headless = headless
        self._browser = None

    async def _get_browser(self):
        """Initialise le navigateur Playwright"""
        try:
            from playwright.async_api import async_playwright
            
            if self._browser is None:
                playwright = await async_playwright().start()
                self._browser = await playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--disable-gpu'
                    ]
                )
            return self._browser
            
        except ImportError:
            raise ScraperError("Playwright non installé. Exécutez: pip install playwright && playwright install")

    async def search_by_name(self, name: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recherche une entreprise par nom et localisation"""
        query = f"{name} {location}" if location else name
        
        try:
            browser = await self._get_browser()
            await self._rate_limit_wait()
            
            context = await browser.new_context(
                user_agent=self.user_agent,
                locale='fr-FR',
                timezone_id='Europe/Paris'
            )
            page = await context.new_page()
            
            # Construire l'URL de recherche
            search_url = f"{self.BASE_URL}/search?q={query.replace(' ', '+')}"
            
            await page.goto(search_url, timeout=self.timeout * 1000, wait_until='domcontentloaded')
            await page.wait_for_timeout(3000)  # Attendre le chargement JS
            
            # Extraire les résultats
            results = await self._extract_results(page)
            
            await context.close()
            return results

        except Exception as e:
            raise ScraperError(f"Google Maps: Erreur - {str(e)}")

    async def _extract_results(self, page) -> List[Dict[str, Any]]:
        """Extrait les résultats de la page Google Maps"""
        try:
            # JavaScript pour extraire les données
            results = await page.evaluate('''
                () => {
                    const results = [];
                    // Selector pour les cartes de résultats (peut changer selon MAJ Google)
                    const cards = document.querySelectorAll('[role="article"], .hfpxzc');
                    
                    cards.forEach(card => {
                        try {
                            const name = card.querySelector('.DUwDvf')?.textContent || 
                                        card.querySelector('.qBF1Pd')?.textContent || '';
                            const address = card.querySelector('.W4Efsd:nth-child(2)')?.textContent || '';
                            const rating = card.querySelector('.MW4etZ')?.textContent || '';
                            const reviews = card.querySelector('.yi40Hd')?.textContent || '';
                            
                            if (name.trim()) {
                                results.push({
                                    nom: name.trim(),
                                    adresse: address.trim(),
                                    note: rating.trim(),
                                    avis: reviews.trim(),
                                    telephone: null,
                                    site_web: null,
                                    horaires: null,
                                    source: 'googlemaps'
                                });
                            }
                        } catch (e) {
                            console.error('Erreur extraction carte:', e);
                        }
                    });
                    
                    return results.slice(0, 10);
                }
            ''')
            
            return results
            
        except Exception as e:
            self.logger.error(f"Google Maps: Erreur extraction - {str(e)}")
            return []

    async def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les détails d'un lieu spécifique"""
        try:
            browser = await self._get_browser()
            await self._rate_limit_wait()
            
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            
            url = f"{self.BASE_URL}/place?place_id={place_id}"
            await page.goto(url, timeout=self.timeout * 1000, wait_until='domcontentloaded')
            await page.wait_for_timeout(3000)
            
            # Extraction des détails
            details = await page.evaluate('''
                () => {
                    return {
                        nom: document.querySelector('.DUwDvf')?.textContent || '',
                        adresse: document.querySelector('.W4Efsd')?.textContent || '',
                        telephone: document.querySelector('[data-item-id="phone"]')?.textContent || '',
                        site_web: document.querySelector('[data-item-id="authority"] a')?.href || '',
                        horaires: document.querySelector('.K4BRSe')?.textContent || '',
                        note: document.querySelector('.F7nice')?.textContent || '',
                    };
                }
            ''')
            
            await context.close()
            return details
            
        except Exception as e:
            self.logger.error(f"Google Maps: Erreur détails - {str(e)}")
            return None

    async def search_by_siret(self, siret: str) -> Optional[Dict[str, Any]]:
        """Recherche par SIRET (non supporté, fallback sur nom)"""
        self.logger.warning("Google Maps: Recherche par SIRET non supportée")
        return None

    async def search_by_siren(self, siren: str) -> Optional[Dict[str, Any]]:
        """Recherche par SIREN (non supporté)"""
        self.logger.warning("Google Maps: Recherche par SIREN non supportée")
        return None

    async def close(self):
        """Ferme le navigateur"""
        if self._browser:
            await self._browser.close()
            self._browser = None
