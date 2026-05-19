"""Modèle Theme — CSS variables en BDD."""
from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from models.database.base import Base, TimestampMixin, UUIDMixin


class Theme(Base, UUIDMixin, TimestampMixin):
    """
    Thème UI complet stocké en BDD.
    css_variables : dict de CSS custom properties (--bg-primary, --accent-blue, etc.)
    """
    __tablename__ = "themes"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author: Mapped[str] = mapped_column(String(100), default="B2B Prospector")
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    preview_color: Mapped[str] = mapped_column(String(20), default="#0d6efd")
    preview_bg: Mapped[str] = mapped_column(String(20), default="#f2f6ff")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    css_variables: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    layout: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<Theme {self.name} active={self.is_active}>"
