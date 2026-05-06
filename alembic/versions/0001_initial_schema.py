"""Initial schema — Phase 1

Revision ID: 0001
Revises:
Create Date: 2026-05-06 10:00:00

Crée toutes les tables : users, pipeline_stages, prospects, contacts,
plugin_states, audit_logs, scrape_cache.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # USERS
    # =========================================================================
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="admin"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # =========================================================================
    # PIPELINE_STAGES
    # =========================================================================
    op.create_table(
        "pipeline_stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("color", sa.String(20), nullable=False, server_default="#3b82f6"),
        sa.Column("order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_won", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_lost", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # =========================================================================
    # PROSPECTS
    # =========================================================================
    op.create_table(
        "prospects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),

        # Identité
        sa.Column("siren", sa.String(9), nullable=True),
        sa.Column("siret", sa.String(14), nullable=True),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("legal_form", sa.String(100), nullable=True),
        sa.Column("naf_code", sa.String(10), nullable=True),
        sa.Column("naf_label", sa.String(255), nullable=True),
        sa.Column("creation_date", sa.Date, nullable=True),
        sa.Column("employee_range", sa.String(50), nullable=True),
        sa.Column("capital", sa.Float, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),

        # Adresse
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("postal_code", sa.String(10), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("department", sa.String(3), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("country", sa.String(2), nullable=False, server_default="FR"),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),

        # Web & contact
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),

        # Pipeline
        sa.Column("stage_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("pipeline_stages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("stage_position", sa.Integer, nullable=False, server_default="0"),

        # Scoring
        sa.Column("digital_score", sa.Float, nullable=True),
        sa.Column("propensity_score", sa.Float, nullable=True),
        sa.Column("propensity_category", sa.String(20), nullable=True),

        # Enrichissement
        sa.Column("enrichment", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("sources_used", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("last_enriched_at", sa.Date, nullable=True),

        # Notes
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("tags", postgresql.JSONB, nullable=False, server_default="[]"),

        # Business
        sa.Column("estimated_revenue", sa.Float, nullable=True),

        # RGPD
        sa.Column("consent_given", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("opt_out", sa.Boolean, nullable=False, server_default=sa.false()),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_prospects_siren", "prospects", ["siren"])
    op.create_index("ix_prospects_siret", "prospects", ["siret"])
    op.create_index("ix_prospects_company_name", "prospects", ["company_name"])
    op.create_index("ix_prospects_city", "prospects", ["city"])
    op.create_index("ix_prospects_stage_id", "prospects", ["stage_id"])
    op.create_index("ix_prospects_search", "prospects", ["company_name", "siren", "siret", "city"])

    # =========================================================================
    # CONTACTS
    # =========================================================================
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("role", sa.String(150), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_contacts_prospect_id", "contacts", ["prospect_id"])

    # =========================================================================
    # PLUGIN_STATES
    # =========================================================================
    op.create_table(
        "plugin_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("config", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_plugin_states_name", "plugin_states", ["name"], unique=True)

    # =========================================================================
    # AUDIT_LOGS
    # =========================================================================
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])

    # =========================================================================
    # SCRAPE_CACHE
    # =========================================================================
    op.create_table(
        "scrape_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("identifier", sa.String(255), nullable=False),
        sa.Column("data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source", "identifier", name="uq_scrape_cache_source_id"),
    )
    op.create_index("ix_scrape_cache_source", "scrape_cache", ["source"])
    op.create_index("ix_scrape_cache_identifier", "scrape_cache", ["identifier"])
    op.create_index("ix_scrape_cache_expires_at", "scrape_cache", ["expires_at"])

    # Activer pg_trgm pour recherche fuzzy
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")


def downgrade() -> None:
    op.drop_table("scrape_cache")
    op.drop_table("audit_logs")
    op.drop_table("plugin_states")
    op.drop_table("contacts")
    op.drop_table("prospects")
    op.drop_table("pipeline_stages")
    op.drop_table("users")
