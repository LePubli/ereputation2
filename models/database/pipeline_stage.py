"""Modèle PipelineStage : étapes du Kanban."""
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.database.base import Base, TimestampMixin, UUIDMixin


class PipelineStage(Base, UUIDMixin, TimestampMixin):
    """
    Étape du pipeline commercial (colonne du Kanban).

    Étapes par défaut (créées au seed) :
        Nouveau → Contacté → RDV pris → En négociation → Gagné / Perdu
    """
    __tablename__ = "pipeline_stages"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    color: Mapped[str] = mapped_column(String(20), default="#3b82f6", nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_won: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_lost: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<PipelineStage {self.order}:{self.name}>"
