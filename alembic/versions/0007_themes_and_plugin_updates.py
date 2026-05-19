"""themes and plugin updates

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-19
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Table themes
    op.create_table(
        "themes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("author", sa.String(100), nullable=False, server_default="B2B Prospector"),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("preview_color", sa.String(20), nullable=False, server_default="#0d6efd"),
        sa.Column("preview_bg", sa.String(20), nullable=False, server_default="#f2f6ff"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("css_variables", JSONB(), nullable=False, server_default="{}"),
        sa.Column("layout", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_themes_is_active", "themes", ["is_active"])
    op.create_index("ix_themes_slug", "themes", ["slug"])

    # Ajouter colonne category + icon sur plugin_states
    op.add_column("plugin_states", sa.Column("category", sa.String(50), nullable=True))
    op.add_column("plugin_states", sa.Column("icon", sa.String(10), nullable=True))
    op.add_column("plugin_states", sa.Column("author", sa.String(100), nullable=True))
    op.add_column("plugin_states", sa.Column("is_core", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_index("ix_themes_is_active", "themes")
    op.drop_index("ix_themes_slug", "themes")
    op.drop_table("themes")
    op.drop_column("plugin_states", "category")
    op.drop_column("plugin_states", "icon")
    op.drop_column("plugin_states", "author")
    op.drop_column("plugin_states", "is_core")
