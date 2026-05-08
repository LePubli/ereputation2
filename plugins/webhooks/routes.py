"""Webhooks sortants — notifie Make/n8n/Zapier sur les événements prospects."""
import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
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


class WebhookCreate(BaseModel):
    name: str
    url: str
    secret: str | None = None
    events: list[str]


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


@router.get("", response_model=list[WebhookRead])
async def list_webhooks(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook).order_by(Webhook.created_at.desc()))
    return [WebhookRead.model_validate(w) for w in result.scalars().all()]


@router.post("", response_model=WebhookRead, status_code=status.HTTP_201_CREATED)
async def create_webhook(body: WebhookCreate, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    invalid = [e for e in body.events if e not in AVAILABLE_EVENTS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Événements invalides: {invalid}")

    wh = Webhook(name=body.name, url=body.url, secret=body.secret, events=body.events)
    db.add(wh)
    await db.commit()
    await db.refresh(wh)
    return WebhookRead.model_validate(wh)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(webhook_id: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    wh = (await db.execute(select(Webhook).where(Webhook.id == webhook_id))).scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook introuvable")
    await db.delete(wh)
    await db.commit()


@router.post("/{webhook_id}/test")
async def test_webhook(webhook_id: UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """Envoie un payload test au webhook."""
    wh = (await db.execute(select(Webhook).where(Webhook.id == webhook_id))).scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook introuvable")

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


async def dispatch_webhook(webhook: "Webhook", event: str, data: dict) -> bool:
    """Envoie le payload à l'URL du webhook avec signature HMAC."""
    payload = json.dumps({"event": event, "timestamp": datetime.now(timezone.utc).isoformat(), "data": data})
    headers = {"Content-Type": "application/json", "X-B2B-Event": event}

    if webhook.secret:
        sig = hmac.new(webhook.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        headers["X-B2B-Signature"] = f"sha256={sig}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook.url, content=payload, headers=headers)
            return response.status_code < 400
    except Exception:
        return False


async def trigger_webhooks(db, event: str, data: dict) -> None:
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
