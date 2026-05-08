"""Modèle Activity — timeline commerciale."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.database.base import Base, TimestampMixin, UUIDMixin

ACTIVITY_TYPES = ("call", "email", "meeting", "note", "task", "linkedin", "other")
ACTIVITY_OUTCOMES = ("positive", "neutral", "negative")


class Activity(Base, UUIDMixin, TimestampMixin):
    """Activité commerciale liée à un prospect (call, email, RDV, note...)."""
    __tablename__ = "activities"

    prospect_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("prospects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    prospect: Mapped["Prospect"] = relationship("Prospect", back_populates="activities")  # type: ignore  # noqa

    def __repr__(self) -> str:
        return f"<Activity {self.type}: {self.title}>"
