from uuid import UUID
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from models.database.base import Base, TimestampMixin, UUIDMixin

class InboundSource(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "inbound_sources"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(String(50), default="webhook", nullable=False)
    field_mapping: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    auto_enrich: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_sequence_id: Mapped[UUID|None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    leads_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
