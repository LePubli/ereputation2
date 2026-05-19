"""
CRM Sync — synchronisation HubSpot/Salesforce/Pipedrive.

Routes exposées (préfixe /api/v1/crm-sync) :
    GET   /config                       → config courante (singleton frontend)
    POST  /config                       → créer/mettre à jour config
    POST  /test                         → test token avant save
    GET   /history?limit=N              → historique jobs sync
    POST  /sync                         → lance un job push/pull
    GET   /jobs/{job_id}                → statut d'un job
    GET   /hubspot/contacts?limit=N     → liste contacts HubSpot (preview)
    GET   /                             → liste toutes les configs (admin)
    POST  /{config_id}/push             → push prospects → CRM
    POST  /{config_id}/pull             → pull contacts → BDD
    GET   /{config_id}/test             → test connexion d'une config
"""
import uuid
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db

router = APIRouter(prefix="/api/v1/crm-sync", tags=["crm_sync"])

HUBSPOT_API = "https://api.hubapi.com"

# Stockage en mémoire des jobs de sync (Phase suivante: BDD)
_SYNC_JOBS: dict[str, dict] = {}


# ─────────────────────────────────────────── Schemas
class CRMConfigBody(BaseModel):
    crm_type: str = "hubspot"
    hubspot_token: str | None = None
    api_key: str | None = None
    field_mapping: dict = {}
    auto_sync: bool = False


class TestTokenBody(BaseModel):
    token: str


class SyncRequest(BaseModel):
    direction: str = "push"  # push / pull / both


# ─────────────────────────────────────────── Config singleton
@router.get("/config")
async def get_config(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """Retourne la config CRM active (ou null)."""
    from models.database.crm_sync_config import CRMSyncConfig

    cfg = (
        await db.execute(
            select(CRMSyncConfig).where(CRMSyncConfig.is_active.is_(True)).limit(1)
        )
    ).scalar_one_or_none()

    if not cfg:
        return None

    return {
        "id": str(cfg.id),
        "crm_type": cfg.crm_type,
        "hubspot_token": "***" if cfg.api_key_encrypted else None,
        "has_token": bool(cfg.api_key_encrypted),
        "field_mapping": cfg.field_mapping or {},
        "is_active": cfg.is_active,
        "last_sync_at": cfg.last_sync_at.isoformat() if cfg.last_sync_at else None,
        "sync_count": cfg.sync_count,
    }


@router.post("/config", status_code=status.HTTP_200_OK)
async def upsert_config(
    body: CRMConfigBody,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Crée ou met à jour la config (singleton par utilisateur)."""
    from models.database.crm_sync_config import CRMSyncConfig

    token = body.hubspot_token or body.api_key

    existing = (
        await db.execute(select(CRMSyncConfig).limit(1))
    ).scalar_one_or_none()

    if existing:
        existing.crm_type = body.crm_type
        if token:
            existing.api_key_encrypted = token
        existing.field_mapping = body.field_mapping or existing.field_mapping
        existing.is_active = True
        await db.commit()
        await db.refresh(existing)
        cfg = existing
    else:
        cfg = CRMSyncConfig(
            name=body.crm_type,
            crm_type=body.crm_type,
            api_key_encrypted=token,
            field_mapping=body.field_mapping or {},
            sync_direction="push",
            is_active=True,
        )
        db.add(cfg)
        await db.commit()
        await db.refresh(cfg)

    return {"id": str(cfg.id), "crm_type": cfg.crm_type, "status": "saved"}


@router.post("/test")
async def test_token(body: TestTokenBody, current_user: CurrentUser):
    """Teste un token HubSpot avant de sauvegarder."""
    ok = await _test_hubspot(body.token)
    return {"connected": ok}


# ─────────────────────────────────────────── History & Sync jobs
@router.get("/history")
async def history(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    """Historique des jobs de synchronisation (memory store + last_sync_at config)."""
    jobs = sorted(
        _SYNC_JOBS.values(),
        key=lambda j: j.get("started_at", ""),
        reverse=True,
    )[:limit]
    return jobs


@router.post("/sync")
async def start_sync(
    body: SyncRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Lance un job de sync (push/pull) — retourne l'id du job pour polling."""
    from models.database.crm_sync_config import CRMSyncConfig
    from models.database.prospect import Prospect
    from models.database.pipeline_stage import PipelineStage

    cfg = (
        await db.execute(
            select(CRMSyncConfig).where(CRMSyncConfig.is_active.is_(True)).limit(1)
        )
    ).scalar_one_or_none()

    if not cfg or not cfg.api_key_encrypted:
        raise HTTPException(400, "Aucune config CRM active")

    job_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc).isoformat()
    _SYNC_JOBS[job_id] = {
        "id": job_id,
        "direction": body.direction,
        "status": "running",
        "started_at": started,
        "pushed": 0,
        "imported": 0,
        "errors": [],
    }

    try:
        if body.direction in ("push", "both"):
            prospects = (
                await db.execute(select(Prospect).limit(200))
            ).scalars().all()
            pushed = 0
            for p in prospects:
                try:
                    if await _push_to_hubspot(p, cfg):
                        pushed += 1
                except Exception as e:
                    _SYNC_JOBS[job_id]["errors"].append(str(e)[:100])
            _SYNC_JOBS[job_id]["pushed"] = pushed
            cfg.sync_count = (cfg.sync_count or 0) + pushed

        if body.direction in ("pull", "both"):
            companies = await _pull_from_hubspot(cfg)
            stage = (
                await db.execute(select(PipelineStage).order_by(PipelineStage.order).limit(1))
            ).scalar_one_or_none()
            imported = 0
            for company in companies:
                props = company.get("properties", {})
                name = props.get("name")
                if not name:
                    continue
                existing = (
                    await db.execute(
                        select(Prospect).where(Prospect.company_name == name)
                    )
                ).scalar_one_or_none()
                if existing:
                    continue
                prospect = Prospect(
                    company_name=name[:500],
                    city=(props.get("city") or "")[:100] or None,
                    phone=(props.get("phone") or "")[:30] or None,
                    website=(props.get("website") or "")[:500] or None,
                    sources_used=["crm_hubspot"],
                    stage_id=stage.id if stage else None,
                )
                db.add(prospect)
                imported += 1
            _SYNC_JOBS[job_id]["imported"] = imported

        cfg.last_sync_at = datetime.now(timezone.utc)
        await db.commit()
        _SYNC_JOBS[job_id]["status"] = "completed"
        _SYNC_JOBS[job_id]["finished_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        _SYNC_JOBS[job_id]["status"] = "failed"
        _SYNC_JOBS[job_id]["errors"].append(str(e)[:200])

    return _SYNC_JOBS[job_id]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, current_user: CurrentUser):
    """Statut d'un job de sync."""
    job = _SYNC_JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


# ─────────────────────────────────────────── HubSpot preview
@router.get("/hubspot/contacts")
async def hubspot_contacts(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """Preview des contacts HubSpot (pour debug/preview UI)."""
    from models.database.crm_sync_config import CRMSyncConfig

    cfg = (
        await db.execute(
            select(CRMSyncConfig).where(CRMSyncConfig.is_active.is_(True)).limit(1)
        )
    ).scalar_one_or_none()

    if not cfg or not cfg.api_key_encrypted:
        raise HTTPException(400, "Aucune config CRM active")

    contacts = await _list_hubspot_contacts(cfg.api_key_encrypted, limit)
    return [
        {
            "id": c.get("id"),
            "email": c.get("properties", {}).get("email"),
            "firstname": c.get("properties", {}).get("firstname"),
            "lastname": c.get("properties", {}).get("lastname"),
            "company": c.get("properties", {}).get("company"),
            "phone": c.get("properties", {}).get("phone"),
        }
        for c in contacts
    ]


# ─────────────────────────────────────────── Admin (legacy multi-config)
@router.get("/")
async def list_configs(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from models.database.crm_sync_config import CRMSyncConfig
    result = await db.execute(select(CRMSyncConfig).order_by(desc(CRMSyncConfig.created_at)))
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "crm_type": c.crm_type,
            "is_active": c.is_active,
            "sync_count": c.sync_count,
            "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
        }
        for c in result.scalars().all()
    ]


@router.post("/{config_id}/push")
async def push_to_crm(
    config_id: UUID,
    prospect_ids: list[UUID],
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.crm_sync_config import CRMSyncConfig
    from models.database.prospect import Prospect

    config = (
        await db.execute(select(CRMSyncConfig).where(CRMSyncConfig.id == config_id))
    ).scalar_one_or_none()
    if not config:
        raise HTTPException(404, "Config CRM introuvable")

    prospects = (
        await db.execute(select(Prospect).where(Prospect.id.in_(prospect_ids)))
    ).scalars().all()

    pushed = 0
    errors = []
    for p in prospects:
        try:
            if config.crm_type == "hubspot" and await _push_to_hubspot(p, config):
                pushed += 1
        except Exception as e:
            errors.append(f"{p.company_name}: {str(e)[:100]}")

    config.sync_count = (config.sync_count or 0) + pushed
    config.last_sync_at = datetime.now(timezone.utc)
    await db.commit()
    return {"pushed": pushed, "total": len(prospects), "errors": errors[:10]}


@router.post("/{config_id}/pull")
async def pull_from_crm(
    config_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.crm_sync_config import CRMSyncConfig
    from models.database.prospect import Prospect
    from models.database.pipeline_stage import PipelineStage

    config = (
        await db.execute(select(CRMSyncConfig).where(CRMSyncConfig.id == config_id))
    ).scalar_one_or_none()
    if not config:
        raise HTTPException(404, "Config CRM introuvable")
    if config.crm_type != "hubspot":
        raise HTTPException(400, "Pull HubSpot uniquement")

    companies = await _pull_from_hubspot(config)
    stage = (
        await db.execute(select(PipelineStage).order_by(PipelineStage.order).limit(1))
    ).scalar_one_or_none()

    imported, skipped = 0, 0
    for company in companies:
        props = company.get("properties", {})
        name = props.get("name")
        if not name:
            skipped += 1
            continue
        existing = (
            await db.execute(select(Prospect).where(Prospect.company_name == name))
        ).scalar_one_or_none()
        if existing:
            skipped += 1
            continue
        prospect = Prospect(
                    company_name=name[:500],
                    city=(props.get("city") or "")[:100] or None,
                    phone=(props.get("phone") or "")[:30] or None,
                    website=(props.get("website") or "")[:500] or None,
                    sources_used=["crm_hubspot"],
                    stage_id=stage.id if stage else None,
                )
        db.add(prospect)
        imported += 1

    config.last_sync_at = datetime.now(timezone.utc)
    await db.commit()
    return {"imported": imported, "skipped": skipped, "total": len(companies)}


@router.get("/{config_id}/test")
async def test_connection(
    config_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.crm_sync_config import CRMSyncConfig
    config = (
        await db.execute(select(CRMSyncConfig).where(CRMSyncConfig.id == config_id))
    ).scalar_one_or_none()
    if not config:
        raise HTTPException(404)
    if config.crm_type == "hubspot":
        ok = await _test_hubspot(config.api_key_encrypted)
        return {"connected": ok, "crm_type": config.crm_type}
    return {"connected": False, "crm_type": config.crm_type}


# ─────────────────────────────────────────── HubSpot helpers
async def _test_hubspot(api_key: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{HUBSPOT_API}/crm/v3/objects/companies",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"limit": 1},
            )
            return r.status_code == 200
    except Exception:
        return False


async def _list_hubspot_contacts(api_key: str, limit: int = 50) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{HUBSPOT_API}/crm/v3/objects/contacts",
                headers={"Authorization": f"Bearer {api_key}"},
                params={
                    "limit": min(limit, 100),
                    "properties": "email,firstname,lastname,company,phone",
                },
            )
            if r.status_code == 200:
                return r.json().get("results", [])
    except Exception:
        pass
    return []


async def _push_to_hubspot(prospect, config) -> bool:
    # Mapping par défaut si vide
    DEFAULT_MAPPING = {
        "company_name": "name",
        "city": "city",
        "phone": "phone",
        "website": "website",
        "siren": "siren_number",
        "region": "state",
        "naf_code": "industry",
    }
    mapping = config.field_mapping or DEFAULT_MAPPING
    field_values = {
        "company_name": prospect.company_name,
        "city": prospect.city or "",
        "phone": prospect.phone or "",
        "website": prospect.website or "",
        "siren": prospect.siren or "",
        "propensity_score": str(getattr(prospect, "propensity_score", "") or ""),
        "naf_code": prospect.naf_code or "",
        "region": prospect.region or "",
    }
    properties = {}
    for our_field, hs_field in mapping.items():
        val = field_values.get(our_field)
        if val:
            properties[hs_field] = val
    if "name" not in properties:
        properties["name"] = prospect.company_name

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            search_r = await client.post(
                f"{HUBSPOT_API}/crm/v3/objects/companies/search",
                headers={
                    "Authorization": f"Bearer {config.api_key_encrypted}",
                    "Content-Type": "application/json",
                },
                json={
                    "filterGroups": [
                        {
                            "filters": [
                                {"propertyName": "name", "operator": "EQ", "value": prospect.company_name}
                            ]
                        }
                    ]
                },
            )
            if search_r.status_code == 200:
                results = search_r.json().get("results", [])
                if results:
                    hs_id = results[0]["id"]
                    r = await client.patch(
                        f"{HUBSPOT_API}/crm/v3/objects/companies/{hs_id}",
                        headers={
                            "Authorization": f"Bearer {config.api_key_encrypted}",
                            "Content-Type": "application/json",
                        },
                        json={"properties": properties},
                    )
                    return r.status_code in (200, 204)
            r = await client.post(
                f"{HUBSPOT_API}/crm/v3/objects/companies",
                headers={
                    "Authorization": f"Bearer {config.api_key_encrypted}",
                    "Content-Type": "application/json",
                },
                json={"properties": properties},
            )
            return r.status_code in (200, 201)
    except Exception:
        return False


async def _pull_from_hubspot(config, limit: int = 100) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{HUBSPOT_API}/crm/v3/objects/companies",
                headers={"Authorization": f"Bearer {config.api_key_encrypted}"},
                params={"limit": min(limit, 100), "properties": "name,city,phone,website"},
            )
            if r.status_code == 200:
                return r.json().get("results", [])
    except Exception:
        pass
    return []
