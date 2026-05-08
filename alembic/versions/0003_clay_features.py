"""Clay features — colonnes dynamiques, séquences email, webhooks, agent logs

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-09
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # COLUMN CONFIGS — colonnes dynamiques du spreadsheet
    # =========================================================================
    op.create_table(
        "column_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),  # insee, bodacc, ai_agent, custom...
        sa.Column("field_path", sa.String(255), nullable=False),  # ex: "enrichment.rating"
        sa.Column("display_type", sa.String(30), default="text", nullable=False),  # text, badge, score, url, phone, email
        sa.Column("order", sa.Integer, default=0, nullable=False),
        sa.Column("is_visible", sa.Boolean, default=True, nullable=False),
        sa.Column("width", sa.Integer, default=180, nullable=False),
        sa.Column("config", postgresql.JSONB, default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # =========================================================================
    # AGENT LOGS — historique des requêtes AI Agent
    # =========================================================================
    op.create_table(
        "agent_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("response", sa.Text, nullable=True),
        sa.Column("model", sa.String(50), default="claude-sonnet-4-20250514", nullable=False),
        sa.Column("tokens_used", sa.Integer, default=0, nullable=False),
        sa.Column("duration_ms", sa.Integer, default=0, nullable=False),
        sa.Column("status", sa.String(20), default="ok", nullable=False),
        sa.Column("field_written", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_logs_prospect_id", "agent_logs", ["prospect_id"])

    # =========================================================================
    # EMAIL SEQUENCES
    # =========================================================================
    op.create_table(
        "sequences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("steps", postgresql.JSONB, default=list, nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "sequence_enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sequence_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sequences.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("current_step", sa.Integer, default=0, nullable=False),
        sa.Column("status", sa.String(20), default="active", nullable=False),  # active/paused/completed/bounced
        sa.Column("next_send_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_seq_enroll_prospect", "sequence_enrollments", ["prospect_id"])
    op.create_index("ix_seq_enroll_next_send", "sequence_enrollments", ["next_send_at"])

    # =========================================================================
    # WEBHOOKS
    # =========================================================================
    op.create_table(
        "webhooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("secret", sa.String(255), nullable=True),
        sa.Column("events", postgresql.JSONB, default=list, nullable=False),  # ["prospect.created", "prospect.enriched"]
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("success_count", sa.Integer, default=0, nullable=False),
        sa.Column("fail_count", sa.Integer, default=0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Champ AI enrichment sur prospects
    op.add_column("prospects", sa.Column(
        "ai_enrichment", postgresql.JSONB, nullable=False, server_default="{}"
    ))


def downgrade() -> None:
    op.drop_column("prospects", "ai_enrichment")
    op.drop_table("webhooks")
    op.drop_table("sequence_enrollments")
    op.drop_table("sequences")
    op.drop_table("agent_logs")
    op.drop_table("column_configs")
