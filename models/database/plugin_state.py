"""Modèle PluginState : état persistant des plugins en BDD."""
from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.database.base import Base, TimestampMixin, UUIDMixin


class PluginState(Base, UUIDMixin, TimestampMixin):
    """Persistance de l'état d'un plugin (activé, config, version)."""
    __tablename__ = "plugin_states"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<PluginState {self.name} active={self.is_active}>"
