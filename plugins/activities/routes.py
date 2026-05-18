"""Routes REST du plugin activities — timeline commerciale."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db
from models.database.activity import Activity
from models.database.prospect import Prospect

router = APIRouter(prefix="/api/v1/activities", tags=["activities"])


class ActivityCreate(BaseModel):
    prospect_id: UUID
    type: str
    title: str
    body: str | None = None
    outcome: str | None = None
    scheduled_at: datetime | None = None
    is_completed: bool = False


class ActivityUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    outcome: str | None = None
    scheduled_at: datetime | None = None
    is_completed: bool | None = None
    completed_at: datetime | None = None


class ActivityRead(BaseModel):
    id: UUID
    prospect_id: UUID
    user_id: UUID | None
    type: str
    title: str
    body: str | None
    outcome: str | None
    scheduled_at: datetime | None
    completed_at: datetime | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# GET "" et "/" acceptent ?prospect_id= (query param)
# GET "/prospect/{id}" conservé pour compat legacy
@router.get("", response_model=list[ActivityRead])
@router.get("/", response_model=list[ActivityRead], include_in_schema=False)
async def list_activities(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    prospect_id: UUID | None = Query(None),
    limit: int = Query(50, le=200),
):
    stmt = select(Activity).order_by(desc(Activity.created_at)).limit(limit)
    if prospect_id:
        stmt = stmt.where(Activity.prospect_id == prospect_id)
    result = await db.execute(stmt)
    return [ActivityRead.model_validate(a) for a in result.scalars().all()]


@router.get("/prospect/{prospect_id}", response_model=list[ActivityRead], include_in_schema=False)
async def list_activities_by_path(
    prospect_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Legacy path param route."""
    stmt = (
        select(Activity)
        .where(Activity.prospect_id == prospect_id)
        .order_by(desc(Activity.created_at))
    )
    result = await db.execute(stmt)
    return [ActivityRead.model_validate(a) for a in result.scalars().all()]


@router.post("", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
async def create_activity(
    data: ActivityCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    prospect = (await db.execute(
        select(Prospect).where(Prospect.id == data.prospect_id)
    )).scalar_one_or_none()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect introuvable")

    activity = Activity(
        prospect_id=data.prospect_id,
        user_id=current_user.id,
        type=data.type,
        title=data.title,
        body=data.body,
        outcome=data.outcome,
        scheduled_at=data.scheduled_at,
        is_completed=data.is_completed,
        completed_at=datetime.now(timezone.utc) if data.is_completed else None,
    )
    db.add(activity)
    prospect.activities_count = (prospect.activities_count or 0) + 1
    prospect.last_activity_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(activity)
    return ActivityRead.model_validate(activity)


@router.patch("/{activity_id}", response_model=ActivityRead)
async def update_activity(
    activity_id: UUID,
    data: ActivityUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    activity = (await db.execute(
        select(Activity).where(Activity.id == activity_id)
    )).scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)
    if data.is_completed and not activity.completed_at:
        activity.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(activity)
    return ActivityRead.model_validate(activity)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    activity = (await db.execute(
        select(Activity).where(Activity.id == activity_id)
    )).scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")

    prospect = (await db.execute(
        select(Prospect).where(Prospect.id == activity.prospect_id)
    )).scalar_one_or_none()
    if prospect and prospect.activities_count:
        prospect.activities_count = max(0, prospect.activities_count - 1)

    await db.delete(activity)
    await db.commit()
    return None
