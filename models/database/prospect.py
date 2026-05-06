"""Modèles Prospect et Contact."""
from datetime import date
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.database.base import Base, TimestampMixin, UUIDMixin


class Prospect(Base, UUIDMixin, TimestampMixin):
    """
    Entreprise prospect (B2B uniquement, RGPD-compatible).
    """
    __tablename__ = "prospects"

    # --- Identité légale (INSEE/SIRENE) ---
    siren: Mapped[str | None] = mapped_column(String(9), index=True, unique=False, nullable=True)
    siret: Mapped[str | None] = mapped_column(String(14), index=True, unique=False, nullable=True)
    company_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    legal_form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    naf_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    naf_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    creation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    employee_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    capital: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Adresse ---
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    department: Mapped[str | None] = mapped_column(String(3), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="FR", nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- Web & contact ---
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- Pipeline ---
    stage_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pipeline_stages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    stage: Mapped["PipelineStage | None"] = relationship(  # type: ignore  # noqa: F821
        "PipelineStage",
        lazy="joined",
    )
    stage_position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # --- Scoring ---
    digital_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    propensity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    propensity_category: Mapped[str | None] = mapped_column(String(20), nullable=True)  # HOT/WARM/COLD

    # --- Données enrichies (sources multiples) ---
    enrichment: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    sources_used: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    last_enriched_at: Mapped[Date | None] = mapped_column(Date, nullable=True)

    # --- Notes & tags ---
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # --- Estimation business ---
    estimated_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- RGPD ---
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opt_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Relations ---
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="prospect",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_prospects_search", "company_name", "siren", "siret", "city"),
    )

    def __repr__(self) -> str:
        return f"<Prospect {self.company_name} ({self.siren})>"


class Contact(Base, UUIDMixin, TimestampMixin):
    """Contact rattaché à un prospect (dirigeant, décideur)."""
    __tablename__ = "contacts"

    prospect_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("prospects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str | None] = mapped_column(String(150), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    prospect: Mapped[Prospect] = relationship("Prospect", back_populates="contacts")

    def __repr__(self) -> str:
        return f"<Contact {self.first_name} {self.last_name}>"
