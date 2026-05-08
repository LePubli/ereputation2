"""
Waterfall Enrichment — orchestration Clay-style.

Principe :
    Pour chaque champ cible, essaie les sources dans l'ordre jusqu'à trouver.
    Comme Clay : Source 1 → vide ? → Source 2 → vide ? → Source 3...

Chaque cellule a un statut :
    "enriched"  → valeur trouvée
    "empty"     → aucune source n'a trouvé
    "error"     → erreur technique
    "pending"   → en cours

Usage :
    result = await waterfall_enrich(prospect, fields=["phone", "website", "ca"])
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class FieldResult:
    """Résultat d'enrichissement pour un champ donné."""
    field: str
    value: Any = None
    source: str = ""
    status: str = "empty"  # enriched / empty / error
    confidence: float = 0.0
    tried_sources: list[str] = field(default_factory=list)


# Définition des cascades par champ
# Ordre = priorité décroissante
WATERFALL_CONFIG: dict[str, list[str]] = {
    "phone":        ["pages_jaunes", "google_maps", "societe_com", "ai_agent"],
    "website":      ["insee", "pappers", "google_maps", "ai_agent"],
    "email":        ["pages_jaunes", "pappers", "ai_agent"],
    "rating":       ["google_maps", "trustpilot"],
    "reviews_count": ["google_maps", "trustpilot"],
    "revenue":      ["societe_com", "ai_agent"],
    "directors":    ["insee", "bodacc", "pappers", "societe_com", "ai_agent"],
    "employee_range": ["insee", "pappers", "ai_agent"],
    "naf_code":     ["insee", "bodacc"],
    "address":      ["insee", "google_maps", "pages_jaunes"],
    "latitude":     ["insee", "google_maps"],
    "longitude":    ["insee", "google_maps"],
    "has_collective_procedure": ["bodacc"],
}


def extract_field_from_result(
    source_result: dict[str, Any],
    field: str,
) -> Any | None:
    """
    Extrait un champ depuis le résultat brut d'un scraper.
    Gère les chemins imbriqués (ex: "bodacc_signals.has_collective_procedure").
    """
    # Champs directs
    direct = source_result.get(field)
    if direct is not None:
        return direct

    # Champs imbriqués dans enrichment
    enrichment = source_result.get("enrichment", {}) or {}
    if field in enrichment:
        return enrichment[field]

    # Champs dans bodacc_signals
    bodacc = source_result.get("bodacc_signals", {}) or {}
    if field in bodacc:
        return bodacc[field]

    # Alias connus
    aliases = {
        "revenue": ["revenue_text", "ca", "chiffre_affaires"],
        "directors": ["directors_names"],
    }
    for alias in aliases.get(field, []):
        val = source_result.get(alias)
        if val is not None:
            return val

    return None


async def waterfall_enrich(
    prospect_dict: dict[str, Any],
    fields: list[str],
    db=None,
    use_ai: bool = True,
    api_key: str | None = None,
) -> dict[str, FieldResult]:
    """
    Enrichit les champs demandés via cascade de sources.

    Args:
        prospect_dict: Données du prospect
        fields: Liste de champs à enrichir
        db: Session SQLAlchemy (pour le cache)
        use_ai: Activer le fallback AI Agent
        api_key: Clé API Anthropic

    Returns:
        dict {field_name: FieldResult}
    """
    from services.scrapers.aggregator import EnrichmentAggregator
    from services.scrapers.societe import SocieteScraper
    from services.scrapers.trustpilot import TrustpilotScraper
    from services.ai_agent import run_agent

    results: dict[str, FieldResult] = {f: FieldResult(field=f) for f in fields}

    # Détermine quelles sources sont nécessaires
    needed_sources: set[str] = set()
    for f in fields:
        cascade = WATERFALL_CONFIG.get(f, [])
        needed_sources.update(s for s in cascade if s != "ai_agent")

    # Lance les scrapers nécessaires en parallèle
    identifier = prospect_dict.get("siret") or prospect_dict.get("siren") or ""
    company_name = prospect_dict.get("company_name", "")
    city = prospect_dict.get("city", "")
    geo_query = f"{company_name}|{city}"

    # Cache des résultats par source
    source_cache: dict[str, dict[str, Any]] = {}

    # Sources SIREN
    if needed_sources & {"insee", "bodacc", "pappers"}:
        aggregator = EnrichmentAggregator(db=db)
        sources_to_run = list(needed_sources & {"insee", "bodacc", "pappers"})
        merged = await aggregator.enrich_by_siret(identifier, sources=sources_to_run)
        for src in sources_to_run:
            source_cache[src] = merged

    # Societe.com
    if "societe_com" in needed_sources and identifier:
        try:
            r = await SocieteScraper().fetch(identifier)
            source_cache["societe_com"] = r.data if r.success else {}
        except Exception as e:
            logger.warning(f"[Waterfall] societe_com error: {e}")
            source_cache["societe_com"] = {}

    # Trustpilot
    if "trustpilot" in needed_sources:
        try:
            r = await TrustpilotScraper().fetch(geo_query)
            source_cache["trustpilot"] = r.data if r.success else {}
        except Exception as e:
            source_cache["trustpilot"] = {}

    # Pages Jaunes + Google Maps (déjà dans aggregator si demandés)
    if needed_sources & {"pages_jaunes", "google_maps"}:
        aggregator2 = EnrichmentAggregator(db=db)
        sources_geo = list(needed_sources & {"pages_jaunes", "google_maps"})
        geo_merged = await aggregator2.enrich_by_siret(
            identifier, sources=sources_geo, use_cache=True
        )
        source_cache["pages_jaunes"] = geo_merged
        source_cache["google_maps"] = geo_merged

    # Applique la cascade pour chaque champ
    for f in fields:
        cascade = WATERFALL_CONFIG.get(f, [])
        result = results[f]

        for source in cascade:
            result.tried_sources.append(source)

            if source == "ai_agent":
                if not use_ai or not api_key:
                    continue
                try:
                    ai_result = await run_agent(
                        prospect_dict,
                        prompt=f"Trouve la valeur du champ '{f}' pour cette entreprise.",
                        api_key=api_key,
                    )
                    if ai_result.get("result") is not None:
                        result.value = ai_result["result"]
                        result.source = "ai_agent"
                        result.status = "enriched"
                        result.confidence = ai_result.get("confidence", 0.7)
                        break
                except Exception as e:
                    logger.warning(f"[Waterfall] AI agent error for {f}: {e}")
                continue

            src_data = source_cache.get(source, {})
            value = extract_field_from_result(src_data, f)

            if value is not None and value != "" and value != [] and value != {}:
                result.value = value
                result.source = source
                result.status = "enriched"
                result.confidence = 0.9
                break

        if result.status == "empty" and result.tried_sources:
            result.status = "empty"

    return results
