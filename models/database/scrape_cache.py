"""Modèle ScrapeCache : évite de re-scraper trop souvent les mêmes données."""
from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.database.base import Base, TimestampMixin, UUIDMixin


class ScrapeCache(Base, UUIDMixin, TimestampMixin):
    """
    Cache d'un scraping pour une (source, identifier) donnée.

    Exemple :
        source="insee", identifier="552120222"  → données entreprise
        source="bodacc", identifier="552120222" → annonces BODACC
    """
    __tablename__ = "scrape_cache"

    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("source", "identifier", name="uq_scrape_cache_source_id"),
    )

    def __repr__(self) -> str:
        return f"<ScrapeCache {self.source}:{self.identifier}>"
