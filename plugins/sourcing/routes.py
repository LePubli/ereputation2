"""Plugin Sourcing — Jobs de scraping multi-sources avec merge enrichi."""
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db

router = APIRouter()

_JOBS: dict[str, dict[str, Any]] = {}

SUPPORTED_SOURCES = {"insee", "pappers", "bodacc", "pages_jaunes", "societe", "trustpilot", "google_maps", "all"}


def _trunc(v: Any, n: int) -> str | None:
    """Tronque une valeur string à n caractères. Retourne None si vide."""
    if v is None:
        return None
    s = str(v).strip()
    return s[:n] if s else None


class SourcingJobConfig(BaseModel):
    region: str | None = None
    naf_code: str | None = None
    city: str | None = None
    query: str | None = None
    limit: int = 100


class SourcingJobCreate(BaseModel):
    name: str
    source: str | None = None         # legacy single-source
    sources: list[str] | None = None  # multi-source
    config: SourcingJobConfig


@router.post("/jobs")
async def create_job(
    payload: SourcingJobCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    if payload.sources:
        sources = [s.lower() for s in payload.sources if s.lower() in SUPPORTED_SOURCES]
    elif payload.source:
        sources = [payload.source.lower()]
    else:
        sources = ["insee"]
    if not sources:
        sources = ["insee"]

    job_id = str(uuid.uuid4())
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    source_label = ",".join(sources)

    job = {
        "id": job_id, "name": payload.name, "source": source_label,
        "sources": sources, "config": payload.config.model_dump(),
        "status": "pending", "progress": 0, "found_count": 0, "new_count": 0,
        "error": None, "created_at": now, "completed_at": None,
    }
    _JOBS[job_id] = job

    try:
        await db.execute(text("""
            INSERT INTO sourcing_jobs (id, name, source, config, status, created_at, created_by)
            VALUES (:id, :name, :source, CAST(:config AS jsonb), :status, :created_at, :created_by)
            ON CONFLICT DO NOTHING
        """), {
            "id": job_id, "name": payload.name, "source": source_label,
            "config": json.dumps({**payload.config.model_dump(), "sources": sources}),
            "status": "pending", "created_at": now, "created_by": str(current_user.id),
        })
        await db.commit()
    except Exception as e:
        logger.warning(f"Could not persist sourcing job: {e}")

    background_tasks.add_task(run_scraping_job, job_id, sources, payload.config)
    return job


@router.get("/jobs")
async def list_jobs(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    db_jobs = []
    try:
        rows = (await db.execute(text("""
            SELECT id, name, source, config, status, progress,
                   found_count, new_count, error, created_at, completed_at
            FROM sourcing_jobs ORDER BY created_at DESC LIMIT :lim
        """), {"lim": limit})).fetchall()
        db_jobs = [
            {
                "id": str(r[0]), "name": r[1], "source": r[2], "config": r[3],
                "status": r[4], "progress": r[5] or 0,
                "found_count": r[6] or 0, "new_count": r[7] or 0,
                "error": r[8],
                "created_at": r[9].isoformat() if hasattr(r[9], "isoformat") else str(r[9]),
                "completed_at": r[10].isoformat() if r[10] and hasattr(r[10], "isoformat") else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.warning(f"DB fetch failed: {e}")

    mem_ids = {j["id"] for j in _JOBS.values()}
    merged = list(_JOBS.values()) + [j for j in db_jobs if j["id"] not in mem_ids]
    merged.sort(key=lambda j: j["created_at"], reverse=True)
    return {"items": merged[:limit], "total": len(merged)}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, current_user: CurrentUser):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job introuvable")
    return job


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, current_user: CurrentUser):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job introuvable")
    if job["status"] == "running":
        job["status"] = "failed"
        job["error"] = "Annulé par l'utilisateur"
    return job


async def _persist_job(job_id: str, status: str, found: int, new: int, error: str | None = None):
    from core.database import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("""
                UPDATE sourcing_jobs
                SET status = :status, progress = 100,
                    found_count = :found, new_count = :new,
                    error = :error, completed_at = :completed
                WHERE id = :id
            """), {
                "id": job_id, "status": status,
                "found": found, "new": new, "error": error,
                "completed": datetime.now(timezone.utc),
            })
            await db.commit()
    except Exception as e:
        logger.warning(f"[Sourcing] DB persist failed: {e}")


async def run_scraping_job(job_id: str, sources: list[str], cfg: SourcingJobConfig):
    """Exécute un job multi-sources avec merge enrichi par SIREN."""
    from core.database import AsyncSessionLocal
    from models.database.prospect import Prospect
    from models.database.pipeline_stage import PipelineStage
    from sqlalchemy import select

    job = _JOBS.get(job_id)
    if not job:
        return
    job["status"] = "running"

    try:
        query_parts = []
        if cfg.naf_code:
            query_parts.append(cfg.naf_code)
        if cfg.city:
            query_parts.append(cfg.city)
        if cfg.region:
            query_parts.append(cfg.region)
        if cfg.query:
            query_parts.append(cfg.query)
        query = " ".join(query_parts) if query_parts else None

        active = set(sources)
        if "all" in active:
            active = {"insee", "pappers", "bodacc"}

        # Step 1 : sources principales (génèrent la liste avec SIREN)
        seed_results: list[dict] = []
        if "insee" in active:
            seed_results.extend(await _scrape_insee(query, cfg))
        if "pappers" in active:
            seed_results.extend(await _scrape_pappers(query, cfg))
        if "bodacc" in active:
            seed_results.extend(await _scrape_bodacc(query, cfg))

        # Fallback INSEE si seules sources d'enrichissement sélectionnées
        if not seed_results and query:
            seed_results = await _scrape_insee(query, cfg)

        # Merge par SIREN
        by_siren: dict[str, dict] = {}
        for r in seed_results:
            siren = r.get("siren")
            if not siren:
                continue
            if siren in by_siren:
                for k, v in r.items():
                    if v and not by_siren[siren].get(k):
                        by_siren[siren][k] = v
            else:
                r["_sources"] = [r.get("_source", "unknown")]
                by_siren[siren] = r

        unique = list(by_siren.values())[: cfg.limit]
        job["found_count"] = len(unique)

        # Step 2 : enrichissement
        enrich_sources = active & {"pages_jaunes", "societe", "trustpilot", "google_maps"}
        if enrich_sources:
            await _enrich_results(unique, enrich_sources)

        # Step 3 : insertion BDD
        new_count = 0
        async with AsyncSessionLocal() as db:
            stage = (
                await db.execute(select(PipelineStage).order_by(PipelineStage.order).limit(1))
            ).scalar_one_or_none()

            for entry in unique:
                siren = entry.get("siren")
                if not siren:
                    continue
                existing = (
                    await db.execute(select(Prospect).where(Prospect.siren == siren))
                ).scalar_one_or_none()
                if existing:
                    updated = False
                    for k in ("phone", "email", "website", "address", "postal_code", "city", "employee_range", "naf_code", "naf_label"):
                        if entry.get(k) and not getattr(existing, k, None):
                            setattr(existing, k, entry[k])
                            updated = True
                    if updated:
                        srcs = list(existing.sources_used or [])
                        for s in entry.get("_sources", []):
                            if s not in srcs:
                                srcs.append(s)
                        existing.sources_used = srcs
                    continue

                prospect = Prospect(
                    company_name=entry.get("company_name") or "Inconnu",
                    siren=siren,
                    siret=entry.get("siret"),
                    naf_code=entry.get("naf_code"),
                    naf_label=entry.get("naf_label"),
                    legal_form=entry.get("legal_form"),
                    address=entry.get("address"),
                    postal_code=entry.get("postal_code"),
                    city=entry.get("city"),
                    department=entry.get("department"),
                    region=entry.get("region"),
                    employee_range=entry.get("employee_range"),
                    phone=entry.get("phone"),
                    email=entry.get("email"),
                    website=entry.get("website"),
                    country="FR",
                    sources_used=entry.get("_sources", list(active)),
                    stage_id=stage.id if stage else None,
                )
                db.add(prospect)
                new_count += 1
            await db.commit()

        job["new_count"] = new_count
        job["status"] = "completed"
        job["progress"] = 100
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
        await _persist_job(job_id, "completed", job["found_count"], new_count)
        logger.info(f"[Sourcing] Job {job_id} : {job['found_count']} trouvés, {new_count} nouveaux, sources={active}")

    except Exception as e:
        logger.exception(f"[Sourcing] Job {job_id} failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)[:200]
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
        await _persist_job(job_id, "failed", job.get("found_count", 0), 0, str(e)[:200])


# ─────────────────────────────────────────── Scrapers seed
async def _scrape_insee(query: str | None, cfg: SourcingJobConfig) -> list[dict]:
    import httpx
    if not query:
        return []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                "https://recherche-entreprises.api.gouv.fr/search",
                params={"q": query, "page": 1, "per_page": min(cfg.limit, 25)},
            )
            if r.status_code != 200:
                return []
            data = r.json()
            results = []
            for e in data.get("results", []):
                siege = e.get("siege") or {}
                cp = siege.get("code_postal") or ""
                results.append({
                    "_source": "insee",
                    "siren": _trunc(e.get("siren"), 9),
                    "siret": _trunc(siege.get("siret"), 14),
                    "company_name": _trunc(e.get("nom_complet") or e.get("nom_raison_sociale"), 500),
                    "naf_code": _trunc(siege.get("activite_principale"), 10),
                    "naf_label": _trunc(e.get("activite_principale_libelle"), 255),
                    "legal_form": _trunc(e.get("nature_juridique_libelle"), 100),
                    "address": _trunc(siege.get("adresse"), 500),
                    "postal_code": _trunc(cp, 10),
                    "city": _trunc(siege.get("libelle_commune"), 100),
                    "department": _trunc(cp[:2] if cp else None, 3),
                    "region": _trunc(siege.get("region"), 100),
                    "employee_range": _trunc(e.get("tranche_effectif_salarie"), 50),
                })
            return results
    except Exception as e:
        logger.warning(f"[INSEE] {e}")
        return []


async def _scrape_pappers(query: str | None, cfg: SourcingJobConfig) -> list[dict]:
    import httpx
    import os
    api_key = os.getenv("PAPPERS_API_KEY")
    if not api_key or not query:
        return []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                "https://api.pappers.fr/v2/recherche",
                params={
                    "api_token": api_key, "q": query,
                    "code_naf": cfg.naf_code or "",
                    "par_page": min(cfg.limit, 100),
                },
            )
            if r.status_code != 200:
                return []
            data = r.json()
            results = []
            for e in data.get("resultats", []):
                siege = e.get("siege") or {}
                cp = siege.get("code_postal") or ""
                results.append({
                    "_source": "pappers",
                    "siren": _trunc(e.get("siren"), 9),
                    "siret": _trunc(siege.get("siret"), 14),
                    "company_name": _trunc(e.get("nom_entreprise"), 500),
                    "naf_code": _trunc(e.get("code_naf"), 10),
                    "naf_label": _trunc(e.get("libelle_code_naf"), 255),
                    "legal_form": _trunc(e.get("forme_juridique"), 100),
                    "address": _trunc(siege.get("adresse_ligne_1"), 500),
                    "postal_code": _trunc(cp, 10),
                    "city": _trunc(siege.get("ville"), 100),
                    "department": _trunc(cp[:2] if cp else None, 3),
                    "employee_range": _trunc(e.get("tranche_effectif"), 50),
                    "phone": _trunc(e.get("telephone"), 30),
                    "email": _trunc(e.get("email"), 255),
                    "website": _trunc(e.get("site_web"), 500),
                })
            return results
    except Exception as e:
        logger.warning(f"[Pappers] {e}")
        return []


async def _scrape_bodacc(query: str | None, cfg: SourcingJobConfig) -> list[dict]:
    import httpx
    if not query:
        return []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                "https://bodacc-datadila.opendatasoft.com/api/records/1.0/search/",
                params={
                    "dataset": "annonces-commerciales",
                    "q": query, "rows": min(cfg.limit, 50),
                    "sort": "-dateparution",
                },
            )
            if r.status_code != 200:
                return []
            data = r.json()
            raw = []
            for rec in data.get("records", []):
                fields = rec.get("fields", {})
                siren = None
                registre = fields.get("registre")
                if isinstance(registre, list) and len(registre) >= 2:
                    cand = str(registre[1] or "").replace(" ", "")
                    if cand.isdigit() and len(cand) == 9:
                        siren = cand
                elif isinstance(registre, str):
                    cand = "".join(c for c in registre if c.isdigit())
                    if len(cand) >= 9:
                        siren = cand[:9]
                name = fields.get("commercant") or fields.get("denomination")
                if not name:
                    continue
                cp = str(fields.get("cp") or "")
                raw.append({
                    "_source": "bodacc",
                    "siren": _trunc(siren, 9),
                    "company_name": _trunc(name, 500),
                    "city": _trunc(fields.get("ville"), 100),
                    "postal_code": _trunc(cp, 10),
                    "department": _trunc(cp[:2] if cp else None, 3),
                    "region": _trunc(fields.get("region_nom_officiel"), 100),
                })
            # Lookup INSEE pour SIREN manquant
            enriched = []
            for r in raw:
                if r.get("siren"):
                    enriched.append(r)
                    continue
                lookup_q = f"{r['company_name']} {r.get('city') or ''}".strip()
                lookup = await _scrape_insee(lookup_q, SourcingJobConfig(limit=1))
                if lookup:
                    merged = {**lookup[0], **{k: v for k, v in r.items() if v}}
                    merged["_source"] = "bodacc+insee"
                    enriched.append(merged)
            return enriched
    except Exception as e:
        logger.warning(f"[BODACC] {e}")
        return []


# ─────────────────────────────────────────── Enrichissement
async def _enrich_results(prospects: list[dict], sources: set[str]):
    semaphore = asyncio.Semaphore(3)

    async def enrich_one(p: dict):
        async with semaphore:
            tasks = []
            if "pages_jaunes" in sources:
                tasks.append(_enrich_pages_jaunes(p))
            if "societe" in sources:
                tasks.append(_enrich_societe(p))
            if "trustpilot" in sources:
                tasks.append(_enrich_trustpilot(p))
            if "google_maps" in sources:
                tasks.append(_enrich_google_maps(p))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    await asyncio.gather(*[enrich_one(p) for p in prospects], return_exceptions=True)


async def _enrich_pages_jaunes(p: dict):
    """Récupère phone depuis le premier résultat Pages Jaunes."""
    try:
        from services.scrapers.pages_jaunes import PagesJaunesScraper
        scraper = PagesJaunesScraper()
        ident = f"{p.get('company_name', '')}|{p.get('city', '')}"
        result = await scraper.fetch(ident)
        if result.success and result.data:
            results_list = result.data.get("results", [])
            if results_list:
                first = results_list[0]
                if first.get("phone") and not p.get("phone"):
                    p["phone"] = _trunc(first["phone"], 30)
                if first.get("address") and not p.get("address"):
                    p["address"] = _trunc(first["address"], 500)
                p.setdefault("_sources", []).append("pages_jaunes")
    except Exception as e:
        logger.debug(f"[PJ enrich] {p.get('company_name')}: {e}")


async def _enrich_societe(p: dict):
    """Données financières + dirigeants depuis Société.com."""
    try:
        from services.scrapers.societe import SocieteScraper
        siren = p.get("siren")
        if not siren:
            return
        scraper = SocieteScraper()
        result = await scraper.fetch(siren)
        if result.success and result.data:
            d = result.data
            extras: dict = {}
            if d.get("revenue_text"):
                extras["revenue_text"] = d["revenue_text"]
            if d.get("directors_names"):
                extras["directors"] = d["directors_names"]
            if extras:
                p["_enrichment"] = {**p.get("_enrichment", {}), **extras}
                p.setdefault("_sources", []).append("societe")
    except Exception as e:
        logger.debug(f"[Societe enrich] {p.get('siren')}: {e}")


async def _enrich_trustpilot(p: dict):
    """Note + nb avis Trustpilot."""
    try:
        from services.scrapers.trustpilot import TrustpilotScraper
        scraper = TrustpilotScraper()
        ident = p.get("website") or p.get("company_name", "")
        result = await scraper.fetch(ident)
        if result.success and result.data:
            d = result.data
            extras: dict = {}
            if d.get("rating"):
                extras["trustpilot_rating"] = d["rating"]
            if d.get("review_count"):
                extras["trustpilot_reviews"] = d["review_count"]
            if extras:
                p["_enrichment"] = {**p.get("_enrichment", {}), **extras}
                p.setdefault("_sources", []).append("trustpilot")
    except Exception as e:
        logger.debug(f"[Trustpilot enrich] {p.get('company_name')}: {e}")


async def _enrich_google_maps(p: dict):
    """Coordonnées GPS + rating Google."""
    try:
        from services.scrapers.google_maps import GoogleMapsScraper
        scraper = GoogleMapsScraper()
        ident = f"{p.get('company_name', '')} {p.get('city', '')}".strip()
        result = await scraper.fetch(ident)
        if result.success and result.data:
            d = result.data
            if d.get("phone") and not p.get("phone"):
                p["phone"] = _trunc(d["phone"], 30)
            if d.get("website") and not p.get("website"):
                p["website"] = _trunc(d["website"], 500)
            if d.get("address") and not p.get("address"):
                p["address"] = _trunc(d["address"], 500)
            p.setdefault("_sources", []).append("google_maps")
    except Exception as e:
        logger.debug(f"[GMaps enrich] {p.get('company_name')}: {e}")
