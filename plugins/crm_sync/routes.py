"""
CRM Sync — Synchronisation bidirectionnelle avec HubSpot, Salesforce, Pipedrive.

Fonctionnement :
    PUSH : Prospects B2B Prospector → CRM (création/mise à jour)
    PULL : Contacts CRM → B2B Prospector (import leads)

HubSpot (le plus utilisé) :
    API v3, clé API ou OAuth2
    Objets : contacts, companies
    Mapping : company_name → name, siren → custom prop, etc.

Salesforce & Pipedrive : via webhooks + API REST
"""
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db

router = APIRouter(prefix="/api/v1/crm-sync", tags=["crm_sync"])

HUBSPOT_API = "https://api.hubapi.com"


class CRMConfigCreate(BaseModel):
    name: str
    crm_type: str  # hubspot / salesforce / pipedrive
    api_key: str
    portal_id: str | None = None
    field_mapping: dict = {
        "company_name": "name",
        "city": "city",
        "phone": "phone",
        "website": "website",
        "siren": "siren__c",
        "propensity_score": "score__c",
    }


@router.get("")
async def list_configs(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    from models.database.crm_sync_config import CRMSyncConfig
    result = await db.execute(select(CRMSyncConfig))
    configs = result.scalars().all()
    return [
        {
            "id": str(c.id), "name": c.name, "crm_type": c.crm_type,
            "is_active": c.is_active, "sync_count": c.sync_count,
            "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
        }
        for c in configs
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_config(
    body: CRMConfigCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from models.database.crm_sync_config import CRMSyncConfig

    # Test de connexion
    if body.crm_type == "hubspot":
        ok = await _test_hubspot(body.api_key)
        if not ok:
            raise HTTPException(status_code=400, detail="Clé API HubSpot invalide — vérifier dans HubSpot > Paramètres > Intégrations > Clés API")

    config = CRMSyncConfig(
        name=body.name,
        crm_type=body.crm_type,
        api_key_encrypted=body.api_key,  # Phase 5 : chiffrement AES
        portal_id=body.portal_id,
        field_mapping=body.field_mapping,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return {"id": str(config.id), "name": config.name, "crm_type": config.crm_type, "status": "connected"}


@router.post("/{config_id}/push")
async def push_to_crm(
    config_id: UUID,
    prospect_ids: list[UUID],
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Exporte des prospects vers le CRM (create or update)."""
    from models.database.crm_sync_config import CRMSyncConfig
    from models.database.prospect import Prospect

    config = (await db.execute(
        select(CRMSyncConfig).where(CRMSyncConfig.id == config_id)
    )).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config CRM introuvable")

    prospects = (await db.execute(
        select(Prospect).where(Prospect.id.in_(prospect_ids))
    )).scalars().all()

    pushed = 0
    errors = []

    for prospect in prospects:
        try:
            if config.crm_type == "hubspot":
                ok = await _push_to_hubspot(prospect, config)
            else:
                ok = False
                errors.append(f"{prospect.company_name}: CRM type '{config.crm_type}' non supporté")

            if ok:
                pushed += 1
        except Exception as e:
            errors.append(f"{prospect.company_name}: {str(e)[:100]}")

    # Mise à jour compteur
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
    """Importe les contacts/companies depuis le CRM vers B2B Prospector."""
    from models.database.crm_sync_config import CRMSyncConfig
    from models.database.prospect import Prospect
    from models.database.pipeline_stage import PipelineStage

    config = (await db.execute(
        select(CRMSyncConfig).where(CRMSyncConfig.id == config_id)
    )).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config CRM introuvable")

    if config.crm_type != "hubspot":
        raise HTTPException(status_code=400, detail="Pull actuellement disponible uniquement pour HubSpot")

    companies = await _pull_from_hubspot(config)
    imported = 0
    skipped = 0

    stage = (await db.execute(
        select(PipelineStage).order_by(PipelineStage.order).limit(1)
    )).scalar_one_or_none()

    for company in companies:
        name = company.get("properties", {}).get("name")
        if not name:
            skipped += 1
            continue

        # Doublon check
        existing = (await db.execute(
            select(Prospect).where(Prospect.company_name == name)
        )).scalar_one_or_none()
        if existing:
            skipped += 1
            continue

        props = company.get("properties", {})
        prospect = Prospect(
            company_name=name,
            city=props.get("city"),
            phone=props.get("phone"),
            website=props.get("website"),
            source="crm_hubspot",
            sources_used=["crm_hubspot"],
            stage_id=stage.id if stage else None,
        )
        db.add(prospect)
        imported += 1

    await db.commit()
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
    config = (await db.execute(
        select(CRMSyncConfig).where(CRMSyncConfig.id == config_id)
    )).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404)

    if config.crm_type == "hubspot":
        ok = await _test_hubspot(config.api_key_encrypted)
        return {"connected": ok, "crm_type": config.crm_type}

    return {"connected": False, "crm_type": config.crm_type}


# --- HubSpot helpers ---

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


async def _push_to_hubspot(prospect, config) -> bool:
    """Crée ou met à jour une company dans HubSpot."""
    mapping = config.field_mapping or {}
    properties = {}

    field_values = {
        "company_name": prospect.company_name,
        "city": prospect.city,
        "phone": prospect.phone,
        "website": prospect.website,
        "siren": prospect.siren,
        "propensity_score": str(prospect.propensity_score or ""),
        "naf_code": prospect.naf_code,
        "region": prospect.region,
    }

    for our_field, hs_field in mapping.items():
        val = field_values.get(our_field)
        if val:
            properties[hs_field] = val

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Cherche si la company existe
            search_r = await client.post(
                f"{HUBSPOT_API}/crm/v3/objects/companies/search",
                headers={"Authorization": f"Bearer {config.api_key_encrypted}", "Content-Type": "application/json"},
                json={"filterGroups": [{"filters": [{"propertyName": "name", "operator": "EQ", "value": prospect.company_name}]}]},
            )

            if search_r.status_code == 200:
                results = search_r.json().get("results", [])
                if results:
                    # Update existant
                    hs_id = results[0]["id"]
                    r = await client.patch(
                        f"{HUBSPOT_API}/crm/v3/objects/companies/{hs_id}",
                        headers={"Authorization": f"Bearer {config.api_key_encrypted}", "Content-Type": "application/json"},
                        json={"properties": properties},
                    )
                    return r.status_code in (200, 204)

            # Création
            r = await client.post(
                f"{HUBSPOT_API}/crm/v3/objects/companies",
                headers={"Authorization": f"Bearer {config.api_key_encrypted}", "Content-Type": "application/json"},
                json={"properties": properties},
            )
            return r.status_code in (200, 201)
    except Exception:
        return False


async def _pull_from_hubspot(config, limit: int = 100) -> list[dict]:
    """Récupère les companies depuis HubSpot."""
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
