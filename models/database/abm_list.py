from uuid import UUID
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from models.database.base import Base, TimestampMixin, UUIDMixin

class ABMList(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "abm_lists"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str|None] = mapped_column(Text, nullable=True)
    criteria: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    prospects_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[UUID|None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

class ABMListProspect(Base):
    __tablename__ = "abm_list_prospects"
    list_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("abm_lists.id", ondelete="CASCADE"), primary_key=True)
    prospect_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("prospects.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    score: Mapped[float|None] = mapped_column(Float, nullable=True)
