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
    jobs = sorted(_JOBS.values(), key=lambda j: j["created_at"], reverse=True)

    if not jobs:
        try:
            rows = (await db.execute(text("""
                SELECT id, name, source, config, status, progress,
                       found_count, new_count, error, created_at, completed_at
                FROM sourcing_jobs ORDER BY created_at DESC LIMIT :lim
            """), {"lim": limit})).fetchall()
            jobs = [
                dict(zip(["id","name","source","config","status","progress",
                          "found_count","new_count","error","created_at","completed_at"], r))
                for r in rows
            ]
        except Exception as e:
            logger.warning(f"DB fallback failed: {e}")

    return {"items": jobs[:limit], "total": len(jobs)}


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


async def run_scraping_job(job_id: str, payload: SourcingJobCreate):
    job = _JOBS.get(job_id)
    if not job:
        return
    job["status"] = "running"
    try:
        await asyncio.sleep(2)
        job["status"] = "completed"
        job["found_count"] = 0
        job["new_count"] = 0
        job["progress"] = 100
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Sourcing job {job_id} completed (placeholder)")
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)[:200]
        logger.error(f"Sourcing job {job_id} failed: {e}")
