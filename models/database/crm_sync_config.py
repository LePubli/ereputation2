from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from models.database.base import Base, TimestampMixin, UUIDMixin

class CRMSyncConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "crm_sync_configs"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    crm_type: Mapped[str] = mapped_column(String(30), nullable=False)
    api_key_encrypted: Mapped[str|None] = mapped_column(Text, nullable=True)
    portal_id: Mapped[str|None] = mapped_column(String(50), nullable=True)
    field_mapping: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    sync_direction: Mapped[str] = mapped_column(String(20), default="push", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
