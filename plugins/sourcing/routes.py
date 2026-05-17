"""Plugin Sourcing — Jobs de scraping en masse."""
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


class SourcingJobConfig(BaseModel):
    region: str | None = None
    naf_code: str | None = None
    city: str | None = None
    query: str | None = None
    limit: int = 100


class SourcingJobCreate(BaseModel):
    name: str
    source: str
    config: SourcingJobConfig


@router.post("/jobs")
async def create_job(
    payload: SourcingJobCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    job = {
        "id": job_id, "name": payload.name, "source": payload.source,
        "config": payload.config.model_dump(), "status": "pending",
        "progress": 0, "found_count": 0, "new_count": 0,
        "error": None, "created_at": now, "completed_at": None,
    }
    _JOBS[job_id] = job

    try:
        await db.execute(text("""
            INSERT INTO sourcing_jobs (id, name, source, config, status, created_at, created_by)
            VALUES (:id, :name, :source, :config::jsonb, :status, :created_at, :created_by)
            ON CONFLICT DO NOTHING
        """), {
            "id": job_id, "name": payload.name, "source": payload.source,
            "config": json.dumps(payload.config.model_dump()),
            "status": "pending", "created_at": now, "created_by": str(current_user.id),
        })
        await db.commit()
    except Exception as e:
        logger.warning(f"Could not persist sourcing job: {e}")

    background_tasks.add_task(run_scraping_job, job_id, payload)
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

    # Merge memory + DB (memory prioritaire pour jobs en cours)
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
    """Met à jour le job en BDD."""
    from core.database import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("""
                UPDATE sourcing_jobs
                SET status = :status, progress = 100,
                    found_count = :found, new_count = :new,
                    error = :error,
                    completed_at = :completed
                WHERE id = :id
            """), {
                "id": job_id, "status": status,
                "found": found, "new": new, "error": error,
                "completed": datetime.now(timezone.utc),
            })
            await db.commit()
    except Exception as e:
        logger.warning(f"[Sourcing] DB persist failed: {e}")


async def run_scraping_job(job_id: str, payload: SourcingJobCreate):
    """Exécute un job de sourcing avec les scrapers réels."""
    from core.database import AsyncSessionLocal
    from models.database.prospect import Prospect
    from models.database.pipeline_stage import PipelineStage
    from sqlalchemy import select

    job = _JOBS.get(job_id)
    if not job:
        return

    job["status"] = "running"
    cfg = payload.config

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

        results = []
        source = payload.source.lower()

        if source in ("insee", "all"):
            results.extend(await _scrape_insee(query, cfg))
        if source in ("pappers", "all"):
            results.extend(await _scrape_pappers(query, cfg))
        if source in ("bodacc", "all"):
            results.extend(await _scrape_bodacc(query, cfg))

        # Dédoublonnage par SIREN
        seen = set()
        unique = []
        for r in results:
            siren = r.get("siren")
            if siren and siren not in seen:
                seen.add(siren)
                unique.append(r)

        unique = unique[: cfg.limit]
        job["found_count"] = len(unique)

        # Insertion en BDD
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
                    continue

                prospect = Prospect(
                    company_name=entry.get("company_name") or entry.get("name") or "Inconnu",
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
                    sources_used=[payload.source],
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
        logger.info(f"[Sourcing] Job {job_id} terminé : {job['found_count']} trouvés, {new_count} nouveaux")

    except Exception as e:
        logger.exception(f"[Sourcing] Job {job_id} failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)[:200]
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
        await _persist_job(job_id, "failed", job.get("found_count", 0), 0, str(e)[:200])


# ─────────────────────────────────────────── Scraper wrappers
async def _scrape_insee(query: str | None, cfg: SourcingJobConfig) -> list[dict]:
    """Recherche INSEE via l'API publique (sans clé)."""
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
                results.append({
                    "siren": e.get("siren"),
                    "siret": siege.get("siret"),
                    "company_name": e.get("nom_complet") or e.get("nom_raison_sociale"),
                    "naf_code": siege.get("activite_principale"),
                    "naf_label": e.get("activite_principale_libelle"),
                    "legal_form": e.get("nature_juridique_libelle"),
                    "address": siege.get("adresse"),
                    "postal_code": siege.get("code_postal"),
                    "city": siege.get("libelle_commune"),
                    "department": siege.get("departement"),
                    "region": siege.get("region"),
                    "employee_range": e.get("tranche_effectif_salarie"),
                })
            return results
    except Exception as e:
        logger.warning(f"[INSEE] {e}")
        return []


async def _scrape_pappers(query: str | None, cfg: SourcingJobConfig) -> list[dict]:
    """Recherche Pappers (nécessite clé API)."""
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
                    "api_token": api_key,
                    "q": query,
                    "code_naf": cfg.naf_code or "",
                    "par_page": min(cfg.limit, 100),
                },
            )
            if r.status_code != 200:
                return []
            data = r.json()
            results = []
            for e in data.get("resultats", []):
                results.append({
                    "siren": e.get("siren"),
                    "siret": e.get("siege", {}).get("siret"),
                    "company_name": e.get("nom_entreprise"),
                    "naf_code": e.get("code_naf"),
                    "naf_label": e.get("libelle_code_naf"),
                    "legal_form": e.get("forme_juridique"),
                    "address": e.get("siege", {}).get("adresse_ligne_1"),
                    "postal_code": e.get("siege", {}).get("code_postal"),
                    "city": e.get("siege", {}).get("ville"),
                    "employee_range": e.get("tranche_effectif"),
                    "phone": e.get("telephone"),
                    "email": e.get("email"),
                    "website": e.get("site_web"),
                })
            return results
    except Exception as e:
        logger.warning(f"[Pappers] {e}")
        return []


async def _scrape_bodacc(query: str | None, cfg: SourcingJobConfig) -> list[dict]:
    """BODACC + lookup INSEE pour récupérer le SIREN par nom si manquant."""
    import httpx
    if not query:
        return []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                "https://bodacc-datadila.opendatasoft.com/api/records/1.0/search/",
                params={
                    "dataset": "annonces-commerciales",
                    "q": query,
                    "rows": min(cfg.limit, 50),
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

                raw.append({
                    "siren": siren,
                    "company_name": name,
                    "city": fields.get("ville"),
                    "postal_code": fields.get("cp"),
                    "department": fields.get("departement_nom_officiel"),
                    "region": fields.get("region_nom_officiel"),
                })

            # Enrichir les résultats sans SIREN via INSEE
            enriched = []
            for r in raw:
                if r.get("siren"):
                    enriched.append(r)
                    continue
                lookup_query = f"{r['company_name']} {r.get('city') or ''}".strip()
                lookup = await _scrape_insee(lookup_query, SourcingJobConfig(limit=1))
                if lookup:
                    merged = {**lookup[0], **{k: v for k, v in r.items() if v}}
                    enriched.append(merged)

            return enriched
    except Exception as e:
        logger.warning(f"[BODACC] {e}")
        return []
