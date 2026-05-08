"""Activities + filtres avancés prospects — Phase 2

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-09 00:00:00
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # TABLE ACTIVITIES — timeline commerciale par prospect
    # =========================================================================
    op.create_table(
        "activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Type : call, email, meeting, note, task, linkedin, other
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("outcome", sa.String(50), nullable=True),   # positive/neutral/negative
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_completed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_activities_prospect_id", "activities", ["prospect_id"])
    op.create_index("ix_activities_type", "activities", ["type"])
    op.create_index("ix_activities_created_at", "activities", ["created_at"])

    # =========================================================================
    # AJOUT COLONNES PROSPECTS — scoring + filtres
    # =========================================================================
    # Prochaine action planifiée
    op.add_column("prospects", sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("prospects", sa.Column("next_action_type", sa.String(30), nullable=True))
    # Scoring détaillé
    op.add_column("prospects", sa.Column("scoring_details", postgresql.JSONB,
                  nullable=False, server_default="{}"))
    # Compteurs
    op.add_column("prospects", sa.Column("activities_count", sa.Integer,
                  nullable=False, server_default="0"))
    op.add_column("prospects", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True))
    # Source de création
    op.add_column("prospects", sa.Column("source", sa.String(30),
                  nullable=False, server_default="manual"))

    op.create_index("ix_prospects_source", "prospects", ["source"])
    op.create_index("ix_prospects_propensity_category", "prospects", ["propensity_category"])
    op.create_index("ix_prospects_naf_code", "prospects", ["naf_code"])
    op.create_index("ix_prospects_region", "prospects", ["region"])

    # =========================================================================
    # TABLE REFRESH TOKENS — pour rotation JWT
    # =========================================================================
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_index("ix_prospects_region", "prospects")
    op.drop_index("ix_prospects_naf_code", "prospects")
    op.drop_index("ix_prospects_propensity_category", "prospects")
    op.drop_index("ix_prospects_source", "prospects")
    op.drop_column("prospects", "last_activity_at")
    op.drop_column("prospects", "activities_count")
    op.drop_column("prospects", "scoring_details")
    op.drop_column("prospects", "next_action_type")
    op.drop_column("prospects", "next_action_at")
    op.drop_column("prospects", "source")
    op.drop_table("activities")
