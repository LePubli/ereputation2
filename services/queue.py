"""
File d'attente ARQ (Async Redis Queue) pour le scraping asynchrone.

Utilisation :
    # Depuis une route FastAPI (non-bloquant) :
    await enqueue_siret_enrichment(prospect_id, identifier)

    # Le worker ARQ tourne en parallèle :
    arq_worker.py

Architecture :
    Route POST /by-siret → enqueue → Redis → ARQ worker → enrichit prospect → 
    → met à jour BDD → publie event Redis pour SSE

Lancement du worker :
    arq services.queue.WorkerSettings
"""
import os
from datetime import datetime, timezone
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from loguru import logger

from core.config import settings


def get_redis_settings() -> RedisSettings:
    """Parse la REDIS_URL en RedisSettings ARQ."""
    url = settings.REDIS_URL
    # Format : redis://:password@host:port/db
    if "://" in url:
        rest = url.split("://", 1)[1]
        if "@" in rest:
            auth, hostport = rest.rsplit("@", 1)
            password = auth.lstrip(":")
        else:
            hostport = rest
            password = None

        if "/" in hostport:
            hostport, db_str = hostport.rsplit("/", 1)
            database = int(db_str)
        else:
            database = 0

        host, port_str = hostport.rsplit(":", 1)
        port = int(port_str)
    else:
        host, port, password, database = "redis", 6379, None, 0

    return RedisSettings(host=host, port=port, password=password, database=database)


async def enqueue_siret_enrichment(prospect_id: str, identifier: str) -> str | None:
    """Enqueue une tâche d'enrichissement SIRET (non-bloquant)."""
    try:
        pool = await create_pool(get_redis_settings())
        job = await pool.enqueue_job(
            "task_enrich_prospect",
            prospect_id=prospect_id,
            identifier=identifier,
        )
        await pool.close()
        logger.info(f"[ARQ] Job enqueued: {job.job_id} pour prospect {prospect_id}")
        return job.job_id
    except Exception as e:
        logger.warning(f"[ARQ] Impossible d'enqueuer (Redis indispo?) : {e}")
        return None


# =============================================================================
# TÂCHES ARQ
# =============================================================================

async def task_enrich_prospect(ctx: dict, prospect_id: str, identifier: str) -> dict:
    """
    Tâche ARQ : enrichit un prospect depuis les scrapers, met à jour la BDD.
    Publie un event Redis pour notifier le frontend via SSE.
    """
    from sqlalchemy import select
    from core.database import AsyncSessionLocal
    from models.database.prospect import Prospect
    from services.scoring import score_prospect
    from services.scrapers.aggregator import EnrichmentAggregator
    from datetime import date

    logger.info(f"[ARQ] Début enrichissement prospect {prospect_id} / identifier {identifier}")

    async with AsyncSessionLocal() as db:
        stmt = select(Prospect).where(Prospect.id == prospect_id)
        prospect = (await db.execute(stmt)).scalar_one_or_none()

        if not prospect:
            logger.warning(f"[ARQ] Prospect {prospect_id} introuvable")
            return {"status": "not_found"}

        try:
            aggregator = EnrichmentAggregator(db=db)
            enrichment = await aggregator.enrich_by_siret(identifier)

            # Mise à jour des champs
            for field in ("company_name", "legal_form", "naf_code", "naf_label",
                          "employee_range", "address", "postal_code", "city",
                          "department", "region", "latitude", "longitude",
                          "website", "phone", "creation_date"):
                new_val = enrichment.get(field)
                if new_val and not getattr(prospect, field, None):
                    setattr(prospect, field, new_val)

            prospect.enrichment = enrichment
            prospect.sources_used = enrichment.get("sources_used", [])
            prospect.last_enriched_at = date.today()

            # Scoring automatique
            await score_prospect(prospect)

            await db.commit()

            # Publier event Redis pour SSE
            try:
                import redis.asyncio as aioredis
                r = aioredis.from_url(settings.REDIS_URL)
                await r.publish(
                    f"prospect:{prospect_id}",
                    f'{{"event":"enriched","prospect_id":"{prospect_id}","status":"ok"}}',
                )
                await r.close()
            except Exception:
                pass  # SSE non critique

            logger.success(f"[ARQ] Prospect {prospect_id} enrichi avec succès")
            return {"status": "ok", "prospect_id": prospect_id}

        except Exception as e:
            logger.exception(f"[ARQ] Erreur enrichissement {prospect_id}")
            return {"status": "error", "error": str(e)}


# =============================================================================
# WORKER SETTINGS
# =============================================================================

class WorkerSettings:
    """Configuration du worker ARQ."""
    functions = [task_enrich_prospect]
    redis_settings = get_redis_settings()
    max_jobs = 10
    job_timeout = 120       # 2 minutes max par job
    keep_result = 3600      # garde le résultat 1h
    queue_name = "arq:queue:b2b"
    on_startup = None
    on_shutdown = None
