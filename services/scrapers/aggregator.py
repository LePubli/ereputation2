"""
Aggregator d'enrichissement multi-sources.

Orchestre les 5 scrapers en parallèle et fusionne les données dans un format
applicatif unifié, prêt à être inséré dans la table `prospects`.

Stratégie de fusion :
1. INSEE = source de vérité pour les données légales (SIREN, NAF, adresse, etc.)
2. BODACC = signaux faibles (procédures collectives, dépôts de comptes)
3. Pappers = web officiel + URL fiche
4. Pages Jaunes = téléphone + adresse contact
5. Google Maps = note, avis, coordonnées GPS, horaires, site web

Cache : ScrapeCache en BDD (TTL 24h par défaut).
"""
import asyncio
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database.scrape_cache import ScrapeCache
from services.scrapers.base import BaseScraper, ScraperResult
from services.scrapers.bodacc import BodaccScraper
from services.scrapers.google_maps import GoogleMapsScraper
from services.scrapers.insee import InseeScraper
from services.scrapers.pages_jaunes import PagesJaunesScraper
from services.scrapers.pappers import PappersScraper


class EnrichmentAggregator:
    """Orchestre l'enrichissement d'un prospect depuis 5 sources."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.scrapers: dict[str, BaseScraper] = {
            "insee": InseeScraper(),
            "bodacc": BodaccScraper(),
            "pappers": PappersScraper(),
            "pages_jaunes": PagesJaunesScraper(),
            "google_maps": GoogleMapsScraper(),
        }

    async def enrich_by_siret(
        self,
        identifier: str,
        sources: list[str] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Enrichit un prospect à partir d'un SIREN/SIRET.

        Étape 1 : INSEE (obligatoire) → on récupère le nom + ville
        Étape 2 : BODACC + Pappers en parallèle (sur SIREN)
        Étape 3 : Pages Jaunes + Google Maps en parallèle (sur Nom + Ville)
        """
        if sources is None:
            sources = ["insee", "bodacc", "pappers", "pages_jaunes", "google_maps"]

        identifier = identifier.replace(" ", "").strip()
        results: dict[str, ScraperResult] = {}

        # ========== Étape 1 : INSEE ==========
        if "insee" in sources:
            results["insee"] = await self._fetch_with_cache("insee", identifier, use_cache)

        insee_data = results.get("insee").data if results.get("insee") and results["insee"].success else {}
        company_name = insee_data.get("company_name") or ""
        city = insee_data.get("city") or ""
        siren = insee_data.get("siren") or identifier[:9]

        # ========== Étape 2 : BODACC + Pappers ==========
        siren_tasks = []
        if "bodacc" in sources:
            siren_tasks.append(("bodacc", siren))
        if "pappers" in sources:
            siren_tasks.append(("pappers", siren))

        if siren_tasks:
            siren_results = await asyncio.gather(
                *[self._fetch_with_cache(s, ident, use_cache) for s, ident in siren_tasks],
                return_exceptions=True,
            )
            for (source, _), res in zip(siren_tasks, siren_results):
                if isinstance(res, Exception):
                    results[source] = ScraperResult(source, success=False, error=str(res))
                else:
                    results[source] = res

        # ========== Étape 3 : Pages Jaunes + Google Maps (si on a un nom) ==========
        if company_name:
            geo_query = f"{company_name}|{city}"
            geo_tasks = []
            if "pages_jaunes" in sources:
                geo_tasks.append(("pages_jaunes", geo_query))
            if "google_maps" in sources:
                geo_tasks.append(("google_maps", geo_query))

            if geo_tasks:
                geo_results = await asyncio.gather(
                    *[self._fetch_with_cache(s, ident, use_cache) for s, ident in geo_tasks],
                    return_exceptions=True,
                )
                for (source, _), res in zip(geo_tasks, geo_results):
                    if isinstance(res, Exception):
                        results[source] = ScraperResult(source, success=False, error=str(res))
                    else:
                        results[source] = res

        # ========== Fusion ==========
        merged = self._merge(results)
        merged["_raw"] = {k: v.dict() for k, v in results.items()}
        return merged

    async def _fetch_with_cache(
        self,
        source: str,
        identifier: str,
        use_cache: bool,
    ) -> ScraperResult:
        """Récupère depuis le cache BDD si valide, sinon scrape."""
        scraper = self.scrapers[source]

        if use_cache and self.db:
            cached = await self._get_cache(source, identifier)
            if cached:
                logger.info(f"[{source}] Cache HIT pour {identifier}")
                return ScraperResult(source, success=True, data=cached, from_cache=True)

        logger.info(f"[{source}] Fetch en live pour {identifier}")
        result = await scraper.fetch(identifier)

        if use_cache and self.db and result.success:
            await self._set_cache(source, identifier, result.data, scraper.cache_ttl())

        return result

    async def _get_cache(self, source: str, identifier: str) -> dict[str, Any] | None:
        """Récupère du cache si non expiré."""
        try:
            stmt = select(ScrapeCache).where(
                ScrapeCache.source == source,
                ScrapeCache.identifier == identifier,
                ScrapeCache.expires_at > datetime.now(timezone.utc),
            )
            result = await self.db.execute(stmt)
            entry = result.scalar_one_or_none()
            return entry.data if entry else None
        except Exception as e:
            logger.warning(f"[Cache] Erreur lecture: {e}")
            return None

    async def _set_cache(self, source: str, identifier: str, data: dict, ttl) -> None:
        """Écrit/met à jour le cache."""
        try:
            now = datetime.now(timezone.utc)
            stmt = select(ScrapeCache).where(
                ScrapeCache.source == source,
                ScrapeCache.identifier == identifier,
            )
            result = await self.db.execute(stmt)
            entry = result.scalar_one_or_none()

            if entry:
                entry.data = data
                entry.fetched_at = now
                entry.expires_at = now + ttl
            else:
                entry = ScrapeCache(
                    source=source,
                    identifier=identifier,
                    data=data,
                    fetched_at=now,
                    expires_at=now + ttl,
                )
                self.db.add(entry)
            await self.db.commit()
        except Exception as e:
            logger.warning(f"[Cache] Erreur écriture: {e}")
            await self.db.rollback()

    @staticmethod
    def _merge(results: dict[str, ScraperResult]) -> dict[str, Any]:
        """
        Fusionne les résultats en un objet applicatif unifié.

        Priorité INSEE > Pappers > Google Maps > Pages Jaunes pour les champs
        en commun. BODACC = enrichissement métadonnées only.
        """
        merged: dict[str, Any] = {
            "sources_used": [],
            "company_name": None,
            "siren": None,
            "siret": None,
            "legal_form": None,
            "naf_code": None,
            "naf_label": None,
            "creation_date": None,
            "employee_range": None,
            "address": None,
            "postal_code": None,
            "city": None,
            "department": None,
            "region": None,
            "latitude": None,
            "longitude": None,
            "website": None,
            "phone": None,
            "rating": None,
            "reviews_count": None,
            "directors": [],
            "bodacc_signals": {},
        }

        # INSEE (référentiel)
        if results.get("insee") and results["insee"].success:
            d = results["insee"].data
            merged["sources_used"].append("insee")
            for k in (
                "company_name", "siren", "siret", "legal_form", "naf_code", "naf_label",
                "creation_date", "employee_range", "address", "postal_code", "city",
                "department", "region", "latitude", "longitude",
            ):
                if d.get(k) is not None:
                    merged[k] = d[k]
            if d.get("directors"):
                merged["directors"] = d["directors"]

        # BODACC (signaux)
        if results.get("bodacc") and results["bodacc"].success:
            merged["sources_used"].append("bodacc")
            merged["bodacc_signals"] = {
                "annonces_count": results["bodacc"].data.get("count", 0),
                "has_collective_procedure": results["bodacc"].data.get("has_collective_procedure", False),
                "last_publication": results["bodacc"].data.get("last_publication"),
                "annonces": results["bodacc"].data.get("annonces", [])[:5],
            }

        # Pappers (site web)
        if results.get("pappers") and results["pappers"].success:
            merged["sources_used"].append("pappers")
            d = results["pappers"].data
            if d.get("website") and not merged.get("website"):
                merged["website"] = d["website"]

        # Pages Jaunes (téléphone)
        if results.get("pages_jaunes") and results["pages_jaunes"].success:
            merged["sources_used"].append("pages_jaunes")
            results_list = results["pages_jaunes"].data.get("results", [])
            if results_list:
                first = results_list[0]
                if first.get("phone") and not merged.get("phone"):
                    merged["phone"] = first["phone"]

        # Google Maps (rating + GPS + site web)
        if results.get("google_maps") and results["google_maps"].success:
            merged["sources_used"].append("google_maps")
            d = results["google_maps"].data
            if d.get("rating") is not None:
                merged["rating"] = d["rating"]
            if d.get("reviews_count") is not None:
                merged["reviews_count"] = d["reviews_count"]
            if d.get("website") and not merged.get("website"):
                merged["website"] = d["website"]
            if d.get("phone") and not merged.get("phone"):
                merged["phone"] = d["phone"]
            if d.get("latitude") and not merged.get("latitude"):
                merged["latitude"] = d["latitude"]
                merged["longitude"] = d["longitude"]

        return merged
