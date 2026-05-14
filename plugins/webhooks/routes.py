"""Webhooks sortants — notifie Make/n8n/Zapier sur les événements prospects."""
import hashlib
import hmac
import json
from collections import deque
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db
from models.database.webhook import Webhook

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

AVAILABLE_EVENTS = [
    "prospect.created",
    "prospect.enriched",
    "prospect.stage_changed",
    "prospect.deleted",
    "activity.created",
]

# Logs ring buffer (les 500 derniers déclenchements)
_WEBHOOK_LOGS: deque = deque(maxlen=500)


class WebhookCreate(BaseModel):
    name: str
    url: str
    secret: str | None = None
    events: list[str]


class WebhookUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    secret: str | None = None
    events: list[str] | None = None
    enabled: bool | None = None
    is_active: bool | None = None


class WebhookRead(BaseModel):
    id: UUID
    name: str
    url: str
    events: list[str]
    is_active: bool
    success_count: int
    fail_count: int
    last_triggered_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("")
@router.get("/")
async def list_webhooks(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(Webhook).order_by(desc(Webhook.created_at)).limit(limit)
    )
    webhooks = result.scalars().all()
    return [
        {
            "id": str(w.id),
            "name": w.name,
            "url": w.url,
            "events": w.events or [],
            "enabled": w.is_active,
            "is_active": w.is_active,
            "success_count": w.success_count,
            "fail_count": w.fail_count,
            "last_triggered_at": w.last_triggered_at.isoformat() if w.last_triggered_at else None,
            "created_at": w.created_at.isoformat(),
        }
        for w in webhooks
    ]


@router.post("")
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_webhook(
    body: WebhookCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    invalid = [e for e in body.events if e not in AVAILABLE_EVENTS]
    if invalid:
        raise HTTPException(400, f"Événements invalides: {invalid}")

    wh = Webhook(name=body.name, url=body.url, secret=body.secret, events=body.events)
    db.add(wh)
    await db.commit()
    await db.refresh(wh)
    return {
        "id": str(wh.id),
        "name": wh.name,
        "url": wh.url,
        "events": wh.events,
        "enabled": wh.is_active,
        "is_active": wh.is_active,
        "success_count": 0,
        "fail_count": 0,
        "created_at": wh.created_at.isoformat(),
    }


@router.patch("/{webhook_id}")
async def update_webhook(
    webhook_id: UUID,
    body: WebhookUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    wh = (await db.execute(select(Webhook).where(Webhook.id == webhook_id))).scalar_one_or_none()
    if not wh:
        raise HTTPException(404, "Webhook introuvable")

    if body.name is not None:
        wh.name = body.name
    if body.url is not None:
        wh.url = body.url
    if body.secret is not None:
        wh.secret = body.secret
    if body.events is not None:
        invalid = [e for e in body.events if e not in AVAILABLE_EVENTS]
        if invalid:
            raise HTTPException(400, f"Événements invalides: {invalid}")
        wh.events = body.events
    if body.enabled is not None:
        wh.is_active = body.enabled
    if body.is_active is not None:
        wh.is_active = body.is_active

    await db.commit()
    await db.refresh(wh)
    return {
        "id": str(wh.id),
        "name": wh.name,
        "url": wh.url,
        "events": wh.events,
        "enabled": wh.is_active,
        "is_active": wh.is_active,
    }


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    wh = (await db.execute(select(Webhook).where(Webhook.id == webhook_id))).scalar_one_or_none()
    if not wh:
        raise HTTPException(404, "Webhook introuvable")
    await db.delete(wh)
    await db.commit()


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Envoie un payload test au webhook."""
    wh = (await db.execute(select(Webhook).where(Webhook.id == webhook_id))).scalar_one_or_none()
    if not wh:
        raise HTTPException(404, "Webhook introuvable")

    payload = {
        "event": "test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"message": "Test depuis B2B Prospector"},
    }
    success = await dispatch_webhook(wh, "test", payload)
    return {"success": success, "url": wh.url}


@router.get("/events")
async def list_events(current_user: CurrentUser):
    return {"events": AVAILABLE_EVENTS}


@router.get("/logs")
async def list_logs(current_user: CurrentUser, limit: int = 100):
    """Logs des dernières exécutions de webhooks (memory ring buffer)."""
    return list(reversed(list(_WEBHOOK_LOGS)))[:limit]


# ─────────────────────────────────────────── Dispatch helpers
async def dispatch_webhook(webhook: Webhook, event: str, data: dict) -> bool:
    payload = json.dumps(
        {"event": event, "timestamp": datetime.now(timezone.utc).isoformat(), "data": data}
    )
    headers = {"Content-Type": "application/json", "X-B2B-Event": event}
    if webhook.secret:
        sig = hmac.new(webhook.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        headers["X-B2B-Signature"] = f"sha256={sig}"

    status_code = 0
    success = False
    error = None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook.url, content=payload, headers=headers)
            status_code = response.status_code
            success = status_code < 400
    except Exception as e:
        error = str(e)[:200]

    _WEBHOOK_LOGS.append({
        "id": str(webhook.id),
        "name": webhook.name,
        "url": webhook.url,
        "event": event,
        "status_code": status_code,
        "success": success,
        "error": error,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    })
    return success


async def trigger_webhooks(db: AsyncSession, event: str, data: dict) -> None:
    """Déclenche tous les webhooks actifs pour un événement donné."""
    stmt = select(Webhook).where(
        Webhook.is_active.is_(True),
        Webhook.events.contains([event]),
    )
    webhooks = (await db.execute(stmt)).scalars().all()

    import asyncio
    results = await asyncio.gather(
        *[dispatch_webhook(wh, event, data) for wh in webhooks],
        return_exceptions=True,
    )
    for wh, ok in zip(webhooks, results):
        if ok is True:
            wh.success_count += 1
        else:
            wh.fail_count += 1
        wh.last_triggered_at = datetime.now(timezone.utc)
    if webhooks:
        await db.commit()
