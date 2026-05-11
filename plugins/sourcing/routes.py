"""
Plugin Sourcing — Gestion des jobs de scraping en masse
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid, logging, asyncio

from core.database import get_db
from core.auth import get_current_active_user
from models.database.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


class SourcingJobConfig(BaseModel):
    region: Optional[str] = None
    naf_code: Optional[str] = None
    city: Optional[str] = None
    query: Optional[str] = None
    limit: int = 100


class SourcingJobCreate(BaseModel):
    name: str
    source: str
    config: SourcingJobConfig


# ─── In-memory job registry (Redis-backed in prod ideally) ───
_JOBS: Dict[str, Dict[str, Any]] = {}


@router.post("/jobs")
async def create_job(
    payload: SourcingJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lance un nouveau job de scraping en arrière-plan"""
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    job = {
        "id": job_id,
        "name": payload.name,
        "source": payload.source,
        "config": payload.config.dict(),
        "status": "pending",
        "progress": 0,
        "found_count": 0,
        "new_count": 0,
        "error": None,
        "created_at": now,
        "completed_at": None,
    }
    _JOBS[job_id] = job

    # Persist to DB
    try:
        db.execute(text("""
            INSERT INTO sourcing_jobs (id, name, source, config, status, created_at, created_by)
            VALUES (:id, :name, :source, :config::jsonb, :status, :created_at, :created_by)
            ON CONFLICT DO NOTHING
        """), {
            "id": job_id, "name": payload.name, "source": payload.source,
            "config": str(payload.config.dict()).replace("'", '"'),
            "status": "pending", "created_at": now, "created_by": str(current_user.id),
        })
        db.commit()
    except Exception as e:
        logger.warning(f"Could not persist sourcing job to DB: {e}")

    # Run scraping in background
    background_tasks.add_task(run_scraping_job, job_id, payload, db)

    return job


@router.get("/jobs")
async def list_jobs(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Liste les jobs récents (mémoire + DB)"""
    jobs = list(_JOBS.values())
    jobs.sort(key=lambda j: j["created_at"], reverse=True)

    # Try DB fallback
    if not jobs:
        try:
            rows = db.execute(text("""
                SELECT id, name, source, config, status, progress,
                       found_count, new_count, error, created_at, completed_at
                FROM sourcing_jobs ORDER BY created_at DESC LIMIT :lim
            """), {"lim": limit}).fetchall()
            jobs = [dict(zip(
                ["id","name","source","config","status","progress",
                 "found_count","new_count","error","created_at","completed_at"], r
            )) for r in rows]
        except Exception:
            pass

    return {"items": jobs[:limit], "total": len(jobs)}


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job introuvable")
    return job


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job introuvable")
    if job["status"] == "running":
        job["status"] = "failed"
        job["error"] = "Annulé par l'utilisateur"
    return job


# ─── Background scraping task ───

async def run_scraping_job(
    job_id: str,
    payload: SourcingJobCreate,
    db: Session,
):
    """Exécute le scraping dans un thread de background"""
    job = _JOBS.get(job_id)
    if not job:
        return

    job["status"] = "running"
    job["progress"] = 5

    try:
        # Import scraper dynamically
        scraper_map = {
            "insee": "services.scrapers.insee",
            "pages_jaunes": "services.scrapers.pages_jaunes",
            "google_maps": "services.scrapers.google_maps",
            "societe": "services.scrapers.societe",
            "pappers": "services.scrapers.pappers",
            "bodacc": "services.scrapers.bodacc",
            "trustpilot": "services.scrapers.trustpilot",
        }

        module_path = scraper_map.get(payload.source)
        if not module_path:
            raise ValueError(f"Source inconnue: {payload.source}")

        import importlib
        module = importlib.import_module(module_path)

        # Build scraper params
        scraper_params = {
            "limit": payload.config.limit,
        }
        if payload.config.region:
            scraper_params["region"] = payload.config.region
        if payload.config.naf_code:
            scraper_params["naf_code"] = payload.config.naf_code
        if payload.config.city:
            scraper_params["city"] = payload.config.city
        if payload.config.query:
            scraper_params["query"] = payload.config.query

        job["progress"] = 15

        # Call scraper (each scraper has a search/scrape function)
        scraper_fn = getattr(module, "scrape", None) or getattr(module, "search", None)
        if not scraper_fn:
            raise ValueError(f"Pas de fonction scrape/search dans {module_path}")

        # Run with asyncio to not block
        results = await asyncio.get_event_loop().run_in_executor(
            None, lambda: scraper_fn(**scraper_params)
        )

        job["progress"] = 70
        found = 0
        new_count = 0

        if results and hasattr(results, '__iter__'):
            for item in results:
                if job.get("status") == "failed":  # Cancelled
                    break
                found += 1

                # Try to insert into prospects table
                try:
                    existing = db.execute(text(
                        "SELECT id FROM prospects WHERE siren = :siren OR (company_name = :name AND city = :city)"
                    ), {
                        "siren": item.get("siren", ""),
                        "name": item.get("company_name", item.get("name", "")),
                        "city": item.get("city", ""),
                    }).fetchone()

                    if not existing:
                        prospect_id = str(uuid.uuid4())
                        company_name = item.get("company_name") or item.get("name") or "Inconnu"
                        db.execute(text("""
                            INSERT INTO prospects (
                                id, company_name, siren, siret, city, region,
                                postal_code, address, phone, email, website,
                                naf_code, naf_label, employee_count,
                                pipeline_stage, score, created_at, updated_at
                            ) VALUES (
                                :id, :company_name, :siren, :siret, :city, :region,
                                :postal_code, :address, :phone, :email, :website,
                                :naf_code, :naf_label, :employee_count,
                                'Nouveau', :score, NOW(), NOW()
                            )
                        """), {
                            "id": prospect_id,
                            "company_name": company_name,
                            "siren": item.get("siren"),
                            "siret": item.get("siret"),
                            "city": item.get("city"),
                            "region": item.get("region"),
                            "postal_code": item.get("postal_code"),
                            "address": item.get("address"),
                            "phone": item.get("phone"),
                            "email": item.get("email"),
                            "website": item.get("website"),
                            "naf_code": item.get("naf_code"),
                            "naf_label": item.get("naf_label"),
                            "employee_count": item.get("employee_count"),
                            "score": item.get("score", 30),
                        })
                        new_count += 1
                        if new_count % 20 == 0:
                            db.commit()
                except Exception as e:
                    logger.debug(f"Insert error for {item}: {e}")

                # Update progress
                if payload.config.limit > 0:
                    pct = min(70 + int((found / payload.config.limit) * 25), 95)
                    job["progress"] = pct

        db.commit()
        job["found_count"] = found
        job["new_count"] = new_count
        job["status"] = "completed"
        job["progress"] = 100
        job["completed_at"] = datetime.utcnow().isoformat()

        # Update DB record
        try:
            db.execute(text("""
                UPDATE sourcing_jobs SET status='completed', found_count=:fc,
                new_count=:nc, completed_at=NOW()
                WHERE id=:id
            """), {"fc": found, "nc": new_count, "id": job_id})
            db.commit()
        except Exception:
            pass

        logger.info(f"Sourcing job {job_id} completed: {found} found, {new_count} new")

    except Exception as e:
        logger.error(f"Sourcing job {job_id} failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)[:200]
        job["progress"] = 0
        try:
            db.execute(text("UPDATE sourcing_jobs SET status='failed', error=:err WHERE id=:id"),
                       {"err": str(e)[:200], "id": job_id})
            db.commit()
        except Exception:
            pass
