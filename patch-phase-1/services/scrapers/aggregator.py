"""
Aggregator - Orchestrateur de scrapers
Fusionne les données de toutes les sources (INSEE, BODACC, Pappers, PagesJaunes, Google Maps)
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .insee import InseeScraper
from .bodacc import BodaccScraper
from .pappers import PappersScraper
from .pages_jaunes import PagesJaunesScraper
from .google_maps import GoogleMapsScraper


class ScraperAggregator:
    """Orchestre l'appel à tous les scrapers et fusionne les résultats"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger("scraper.aggregator")
        
        # Initialisation des scrapers avec configuration
        self.insee = InseeScraper(
            rate_limit=self.config.get('insee_rate_limit', 10),
            timeout=self.config.get('timeout', 30)
        )
        self.bodacc = BodaccScraper(
            rate_limit=self.config.get('bodacc_rate_limit', 5),
            timeout=self.config.get('timeout', 30)
        )
        self.pappers = PappersScraper(
            rate_limit=self.config.get('pappers_rate_limit', 2),
            timeout=self.config.get('timeout', 30)
        )
        self.pagesjaunes = PagesJaunesScraper(
            rate_limit=self.config.get('pagesjaunes_rate_limit', 1),
            timeout=self.config.get('timeout', 60)
        )
        self.googlemaps = GoogleMapsScraper(
            rate_limit=self.config.get('googlemaps_rate_limit', 1),
            timeout=self.config.get('timeout', 60),
            headless=self.config.get('playwright_headless', True)
        )

    async def scrape_all(self, siret: Optional[str] = None, siren: Optional[str] = None, 
                         name: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrappe toutes les sources disponibles pour une entreprise
        Priorité: SIRET > SIREN > Nom + Location
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "sources_queried": [],
            "sources_success": [],
            "sources_failed": [],
            "data": {}
        }

        # Déterminer l'identifiant principal
        identifier = siret or siren
        if not identifier and not name:
            raise ValueError("SIRET, SIREN ou Nom requis")

        # Lancer tous les scrapers en parallèle
        tasks = []

        # INSEE (toujours en premier - le plus fiable)
        if identifier:
            if len(identifier) == 14:  # SIRET
                tasks.append(("insee", self.insee.search_by_siret(identifier)))
            else:  # SIREN
                tasks.append(("insee", self.insee.search_by_siren(identifier)))
        elif name:
            tasks.append(("insee", self._wrap_results(self.insee.search_by_name(name, location))))

        # BODACC (si SIREN disponible)
        if siren or (siret and len(siret) >= 9):
            siren_val = siren or siret[:9]
            tasks.append(("bodacc", self._wrap_results(self.bodacc.search_by_siren(siren_val))))

        # Pappers (scraping HTTP - plus lent)
        if identifier:
            if len(identifier) == 14:
                tasks.append(("pappers", self._wrap_optional(self.pappers.search_by_siret(identifier))))
            else:
                tasks.append(("pappers", self._wrap_optional(self.pappers.search_by_siren(identifier))))

        # Pages Jaunes (si nom disponible)
        if name:
            tasks.append(("pagesjaunes", self._wrap_results(self.pagesjaunes.search_by_name(name, location))))

        # Google Maps (si nom disponible - le plus lent)
        if name and self.config.get('enable_googlemaps', False):
            tasks.append(("googlemaps", self._wrap_results(self.googlemaps.search_by_name(name, location))))

        # Exécution parallèle
        if tasks:
            completed = await asyncio.gather(
                *[task[1] for task in tasks],
                return_exceptions=True
            )

            for i, (source_name, _) in enumerate(tasks):
                results["sources_queried"].append(source_name)
                result = completed[i]

                if isinstance(result, Exception):
                    results["sources_failed"].append(source_name)
                    self.logger.error(f"{source_name}: {str(result)}")
                else:
                    results["sources_success"].append(source_name)
                    results["data"][source_name] = result

        # Fusionner les données
        merged = self._merge_data(results["data"])
        results["merged"] = merged

        # Nettoyer le navigateur Google Maps
        try:
            await self.googlemaps.close()
        except:
            pass

        return results

    async def _wrap_results(self, coro):
        """Wrapper pour les coroutines retournant des listes"""
        return await coro

    async def _wrap_optional(self, coro):
        """Wrapper pour les coroutines retournant Optional"""
        return await coro

    def _merge_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fusionne intelligemment les données de toutes les sources"""
        merged = {
            "siret": None,
            "siren": None,
            "raison_sociale": None,
            "nom_commercial": None,
            "adresse": None,
            "code_postal": None,
            "ville": None,
            "telephone": None,
            "email": None,
            "site_web": None,
            "secteur_activite": None,
            "code_naf": None,
            "effectif": None,
            "date_creation": None,
            "dirigeants": [],
            "bodacc_mentions": [],
            "pappers_data": None,
            "pagesjaunes_data": [],
            "googlemaps_data": []
        }

        # Priorité INSEE pour les données légales
        if "insee" in data and data["insee"]:
            insee_data = data["insee"]
            if isinstance(insee_data, dict):
                merged.update({
                    "siret": insee_data.get("siret"),
                    "siren": insee_data.get("siren"),
                    "raison_sociale": insee_data.get("raison_sociale"),
                    "nom_commercial": insee_data.get("nom_commercial"),
                    "adresse": insee_data.get("adresse"),
                    "code_postal": insee_data.get("code_postal"),
                    "ville": insee_data.get("ville"),
                    "telephone": insee_data.get("telephone"),
                    "email": insee_data.get("email"),
                    "site_web": insee_data.get("site_web"),
                    "secteur_activite": insee_data.get("secteur_activite"),
                    "code_naf": insee_data.get("code_naf"),
                    "effectif": insee_data.get("effectif"),
                    "date_creation": insee_data.get("date_creation"),
                    "dirigeants": insee_data.get("dirigeants", [])
                })

        # BODACC mentions
        if "bodacc" in data and data["bodacc"]:
            merged["bodacc_mentions"] = data["bodacc"] if isinstance(data["bodacc"], list) else [data["bodacc"]]

        # Pappers data
        if "pappers" in data and data["pappers"]:
            merged["pappers_data"] = data["pappers"]

        # Pages Jaunes - prendre le premier résultat pertinent
        if "pagesjaunes" in data and data["pagesjaunes"]:
            pj_list = data["pagesjaunes"] if isinstance(data["pagesjaunes"], list) else [data["pagesjaunes"]]
            merged["pagesjaunes_data"] = pj_list[:5]  # Garder les 5 premiers
            
            # Compléter téléphone si manquant
            if not merged["telephone"] and pj_list and pj_list[0].get("telephone"):
                merged["telephone"] = pj_list[0]["telephone"]

        # Google Maps - prendre le premier résultat pertinent
        if "googlemaps" in data and data["googlemaps"]:
            gm_list = data["googlemaps"] if isinstance(data["googlemaps"], list) else [data["googlemaps"]]
            merged["googlemaps_data"] = gm_list[:5]

        return merged

    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de tous les scrapers"""
        return {
            "insee": await self.insee.get_stats(),
            "bodacc": await self.bodacc.get_stats(),
            "pappers": await self.pappers.get_stats(),
            "pagesjaunes": await self.pagesjaunes.get_stats(),
            "googlemaps": await self.googlemaps.get_stats()
        }
