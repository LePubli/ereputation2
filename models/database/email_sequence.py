from datetime import datetime
from uuid import UUID
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.database.base import Base, TimestampMixin, UUIDMixin


class SequenceStep(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sequence_steps"
    sequence_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("email_sequences.id", ondelete="CASCADE"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    wait_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subject_template: Mapped[str] = mapped_column(Text, nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    use_ai_personalization: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_personalization_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence: Mapped["EmailSequence"] = relationship("EmailSequence", back_populates="steps")


class EmailSequence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "email_sequences"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    steps: Mapped[list["SequenceStep"]] = relationship("SequenceStep", back_populates="sequence", cascade="all, delete-orphan")


class SequenceContact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sequence_contacts"
    sequence_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("email_sequences.id", ondelete="CASCADE"), nullable=False, index=True)
    prospect_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    next_send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    open_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reply_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bounced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seq_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class EmailSend(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "email_sends"
    sequence_contact_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sequence_contacts.id", ondelete="CASCADE"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    tracking_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
