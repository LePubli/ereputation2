"""
Plugin Scraper INSEE - Récupération des données légales d'entreprises
Utilise l'API INSEE en priorité, avec fallback sur Pappers/BODACC
"""
import httpx
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

from core.config import settings
from core.event_bus import event_bus


class INSEEService:
    """Service pour interagir avec l'API INSEE"""
    
    def __init__(self):
        self.base_url = "https://api.insee.fr"
        self.token_url = "https://api.insee.fr/token"
        self.api_key = settings.INSEE_API_KEY
        self.api_secret = settings.INSEE_API_SECRET
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
    
    async def get_access_token(self) -> Optional[str]:
        """Obtient un token d'accès à l'API INSEE"""
        if not self.api_key or not self.api_secret:
            return None
        
        # Vérifie si le token est encore valide
        if self._access_token and self._token_expiry:
            if datetime.utcnow() < self._token_expiry:
                return self._access_token
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data={"grant_type": "client_credentials"},
                    auth=(self.api_key, self.api_secret),
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self._access_token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                    return self._access_token
                    
        except Exception as e:
            logger.error(f"Failed to get INSEE token: {e}")
        
        return None
    
    async def get_company_by_siret(self, siret: str) -> Optional[Dict[str, Any]]:
        """Récupère les données d'une entreprise par SIRET"""
        token = await self.get_access_token()
        if not token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/entreprises/siret/{siret}",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"date": datetime.utcnow().strftime("%Y-%m-%d")},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"SIRET {siret} not found in INSEE")
                    return None
                else:
                    logger.error(f"INSEE API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to fetch company from INSEE: {e}")
            return None
    
    async def search_company(self, query: str) -> List[Dict[str, Any]]:
        """Recherche des entreprises par nom ou SIREN"""
        token = await self.get_access_token()
        if not token:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/entreprises/rechercher",
                    headers={"Authorization": f"Bearer {token}"},
                    params={
                        "q": query,
                        "nombre": 10,
                        "page": 1
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("resultats", [])
                    
        except Exception as e:
            logger.error(f"Failed to search companies in INSEE: {e}")
        
        return []


class PappersService:
    """Service fallback pour interagir avec l'API Pappers"""
    
    def __init__(self):
        self.base_url = "https://api.pappers.fr/v1"
        self.api_key = settings.PAPPERS_API_KEY
    
    async def get_company_by_siren(self, siren: str) -> Optional[Dict[str, Any]]:
        """Récupère les données d'une entreprise par SIREN"""
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/entreprise",
                    params={"siren": siren, "cle_api": self.api_key},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"Failed to fetch company from Pappers: {e}")
        
        return None
    
    async def search_company(self, query: str) -> List[Dict[str, Any]]:
        """Recherche des entreprises par nom"""
        if not self.api_key:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/recherche",
                    params={"q": query, "cle_api": self.api_key, "limite": 10},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("entreprises", [])
                    
        except Exception as e:
            logger.error(f"Failed to search companies in Pappers: {e}")
        
        return []


class ScraperINSEEPlugin:
    """Plugin principal pour la récupération des données légales"""
    
    def __init__(self):
        self.insee_service = INSEEService()
        self.pappers_service = PappersService()
    
    def parse_insee_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforme les données INSEE en format standardisé"""
        etablissement = data.get("etablissement", {})
        unite_legale = data.get("uniteLegale", {})
        
        return {
            "siret": etablissement.get("siret"),
            "siren": unite_legale.get("siren"),
            "raison_sociale": unite_legale.get("denominationUniteLegale") or 
                             unite_legale.get("nomUniteLegale", ""),
            "enseigne": etablissement.get("enseignePremiereEtablissement", ""),
            "adresse": {
                "numero": etablissement.get("numeroVoieEtablissement", ""),
                "voie": etablissement.get("typeVoieEtablissement", "") + " " + 
                       etablissement.get("libelleVoieEtablissement", ""),
                "complement": etablissement.get("complementAdresseEtablissement", ""),
                "code_postal": etablissement.get("codePostalEtablissement", ""),
                "ville": etablissement.get("libelleCommuneEtablissement", ""),
                "pays": "FR"
            },
            "code_naf": unite_legale.get("activitePrincipaleUniteLegale", ""),
            "libelle_naf": "",  # À enrichir avec la nomenclature NAF
            "forme_juridique": unite_legale.get("categorieJuridiqueUniteLegale", ""),
            "effectifs": str(etablissement.get("trancheEffectifsEtablissement", "")),
            "date_creation": unite_legale.get("dateCreationUniteLegale", ""),
            "etat_administratif": etablissement.get("etatAdministratifEtablissement", ""),
            "actif": etablissement.get("etatAdministratifEtablissement") == "A",
            "siege_social": etablissement.get("siegeEtablissement", False),
            "source": "INSEE",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def parse_pappers_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforme les données Pappers en format standardisé"""
        return {
            "siret": data.get("siren"),  # Pappers retourne SIREN au niveau entreprise
            "siren": data.get("siren"),
            "raison_sociale": data.get("nom", ""),
            "enseigne": data.get("nom_commercial", ""),
            "adresse": {
                "numero": "",
                "voie": data.get("adresse_rue", ""),
                "complement": data.get("adresse_complement", ""),
                "code_postal": data.get("code_postal", ""),
                "ville": data.get("localite", ""),
                "pays": "FR"
            },
            "code_naf": data.get("code_activite_principale", ""),
            "libelle_naf": data.get("activite_principale", ""),
            "forme_juridique": data.get("forme_juridique", ""),
            "effectifs": str(data.get("effectifs", "")),
            "date_creation": data.get("date_creation", ""),
            "etat_administratif": "A" if data.get("active", True) else "F",
            "actif": data.get("active", True),
            "siege_social": True,
            "source": "PAPPERS",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def fetch_company_data(self, siret: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les données d'une entreprise par SIRET
        Utilise INSEE en priorité, puis Pappers en fallback
        """
        # Essai INSEE (nécessite SIRET complet)
        if self.insee_service.api_key:
            logger.info(f"Fetching SIRET {siret} from INSEE")
            insee_data = await self.insee_service.get_company_by_siret(siret)
            if insee_data:
                parsed = self.parse_insee_data(insee_data)
                await event_bus.publish("prospect.legal_updated", {
                    "siret": siret,
                    "data": parsed
                })
                return parsed
        
        # Fallback Pappers (avec SIREN extrait du SIRET)
        if Path(settings.PLUGINS_DIR).joinpath("scraper-insee").exists():
            siren = siret[:9] if len(siret) >= 9 else siret
            logger.info(f"Fetching SIREN {siren} from Pappers (fallback)")
            
            pappers_data = await self.pappers_service.get_company_by_siren(siren)
            if pappers_data:
                parsed = self.parse_pappers_data(pappers_data)
                parsed["siret"] = siret  # Force le SIRET demandé
                await event_bus.publish("prospect.legal_updated", {
                    "siret": siret,
                    "data": parsed
                })
                return parsed
        
        logger.warning(f"No data found for SIRET {siret}")
        return None
    
    async def search_companies(self, query: str) -> List[Dict[str, Any]]:
        """Recherche des entreprises par nom ou SIREN"""
        results = []
        
        # Recherche INSEE
        if self.insee_service.api_key:
            logger.info(f"Searching '{query}' in INSEE")
            insee_results = await self.insee_service.search_company(query)
            for item in insee_results:
                etablissement = item.get("etablissement", {})
                results.append({
                    "siret": etablissement.get("siret", ""),
                    "siren": item.get("siren", ""),
                    "raison_sociale": item.get("denominationUniteLegale", 
                                              item.get("nomUniteLegale", "")),
                    "ville": etablissement.get("libelleCommuneEtablissement", ""),
                    "actif": etablissement.get("etatAdministratifEtablissement") == "A",
                    "source": "INSEE"
                })
        
        # Recherche Pappers si aucun résultat INSEE
        if not results and self.pappers_service.api_key:
            logger.info(f"Searching '{query}' in Pappers (fallback)")
            pappers_results = await self.pappers_service.search_company(query)
            for item in pappers_results:
                results.append({
                    "siret": item.get("siren", ""),
                    "siren": item.get("siren", ""),
                    "raison_sociale": item.get("nom", ""),
                    "ville": item.get("localite", ""),
                    "actif": item.get("active", True),
                    "source": "PAPPERS"
                })
        
        await event_bus.publish("prospect.search_performed", {
            "query": query,
            "results_count": len(results)
        })
        
        return results


class ScraperINSEE(ScraperINSEEPlugin):
    """Facade rétrocompatible autour de ScraperINSEEPlugin."""

    def __init__(self):
        super().__init__()
        self.use_insee = True
        self.insee_token: Optional[str] = None
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def _get_insee_token(self) -> Optional[str]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.insee_service.token_url,
                data={"grant_type": "client_credentials"},
                timeout=10.0,
            )
        token = response.json().get("access_token")
        self.insee_token = token
        return token

    async def _fetch_from_pappers(self, siren: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.pappers_service.base_url}/entreprise",
                params={"siren": siren, "cle_api": self.pappers_service.api_key},
                timeout=10.0,
            )
        if response.status_code == 200:
            return self.parse_pappers_data(response.json())
        return None

    async def fetch_company_data(self, identifier: str) -> Optional[Dict[str, Any]]:
        if not self._validate_siren(identifier) and not (identifier.isdigit() and len(identifier) == 14):
            raise ValueError("Invalid SIREN/SIRET")

        cached = self._cache_get(identifier)
        if cached:
            return cached

        if self.use_insee:
            token = self.insee_token or await self._get_insee_token()
            if token:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.insee_service.base_url}/entreprises/siret/{identifier}",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10.0,
                    )
                if response.status_code == 404:
                    raise LookupError(f"Company {identifier} not found")
                if response.status_code == 200:
                    parsed = self.parse_insee_data(response.json())
                    self._cache_set(identifier, parsed)
                    return parsed

        siren = identifier[:9]
        parsed = await self._fetch_from_pappers(siren)
        if parsed:
            self._cache_set(identifier, parsed)
        return parsed

    async def search_by_name(self, query: str) -> List[Dict[str, Any]]:
        if not self._validate_query(query):
            return []
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.insee_service.base_url}/entreprises/rechercher",
                params={"q": query},
                timeout=10.0,
            )
        if response.status_code == 200:
            data = response.json()
            return data.get("results", data.get("resultats", []))
        return []

    async def search_by_naf(self, naf_code: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.insee_service.base_url}/entreprises/rechercher",
                params={"naf": naf_code},
                timeout=10.0,
            )
        if response.status_code == 200:
            data = response.json()
            return data.get("results", data.get("resultats", []))
        return []

    @staticmethod
    def _validate_siren(siren: str) -> bool:
        return siren.isdigit() and len(siren) == 9

    @staticmethod
    def _siren_to_siret(siren: str, nic: str) -> str:
        return f"{siren}{nic}"

    @staticmethod
    def _validate_query(query: str) -> bool:
        return len(query) >= 3 and "<" not in query and ">" not in query

    def _cache_set(self, key: str, value: Dict[str, Any]) -> None:
        self._cache[key] = value

    def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(key)


# Instance globale du plugin
plugin_instance = ScraperINSEEPlugin()


def init():
    """Initialisation du plugin"""
    logger.info("Initializing scraper-insee plugin")


def cleanup():
    """Nettoyage du plugin"""
    logger.info("Cleaning up scraper-insee plugin")


# Handlers pour les endpoints API
async def create_prospect(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handler POST /api/v1/prospects - Créer un prospect par SIRET"""
    siret = request_data.get("siret")
    
    if not siret or not siret.isdigit() or len(siret) != 14:
        return {
            "error": "SIRET invalide. Doit contenir 14 chiffres.",
            "status_code": 400
        }
    
    # Récupère les données de l'entreprise
    company_data = await plugin_instance.fetch_company_data(siret)
    
    if not company_data:
        return {
            "error": f"Aucune entreprise trouvée pour le SIRET {siret}",
            "status_code": 404
        }
    
    if not company_data.get("actif"):
        return {
            "error": f"L'entreprise avec SIRET {siret} n'est plus active",
            "status_code": 400,
            "data": company_data
        }
    
    # Émet l'événement prospect.created
    await event_bus.publish("prospect.created", {
        "siret": siret,
        "company_data": company_data
    })
    
    return {
        "success": True,
        "data": company_data,
        "message": f"Prospect créé avec succès pour {company_data['raison_sociale']}"
    }


async def get_prospect_legal(siren: str) -> Dict[str, Any]:
    """Handler GET /api/v1/prospects/{siren} - Récupérer infos légales"""
    # Pour cette implémentation, on utilise le SIREN comme identifiant
    # Dans une vraie implémentation, il faudrait mapper SIREN -> SIRET
    return {
        "error": "Endpoint à implémenter avec base de données",
        "siren": siren
    }


async def search_prospects(query: str) -> Dict[str, Any]:
    """Handler GET /api/v1/prospects/search - Rechercher entreprises"""
    if not query or len(query) < 2:
        return {
            "error": "Query trop courte (minimum 2 caractères)",
            "status_code": 400
        }
    
    results = await plugin_instance.search_companies(query)
    
    return {
        "query": query,
        "count": len(results),
        "results": results
    }
