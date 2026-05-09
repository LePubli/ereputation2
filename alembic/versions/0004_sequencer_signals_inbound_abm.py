"""Phase 4 — Sequencer, Signals, Inbound, ABM, CRM Sync

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-09
"""
from typing import Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # EMAIL SEQUENCES — remplace la table partielle de 0003
    # =========================================================================
    op.create_table(
        "email_sequences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "sequence_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sequence_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("email_sequences.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("wait_days", sa.Integer, default=0, nullable=False),  # jours après étape précédente
        sa.Column("subject_template", sa.Text, nullable=False),         # "Bonjour {{company_name}}"
        sa.Column("body_template", sa.Text, nullable=False),            # Corps avec variables
        sa.Column("use_ai_personalization", sa.Boolean, default=False, nullable=False),
        sa.Column("ai_personalization_prompt", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "sequence_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sequence_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("email_sequences.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("current_step", sa.Integer, default=0, nullable=False),
        sa.Column("status", sa.String(20), default="active", nullable=False),
        sa.Column("next_send_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_count", sa.Integer, default=0, nullable=False),
        sa.Column("open_count", sa.Integer, default=0, nullable=False),
        sa.Column("reply_count", sa.Integer, default=0, nullable=False),
        sa.Column("bounced", sa.Boolean, default=False, nullable=False),
        sa.Column("unsubscribed", sa.Boolean, default=False, nullable=False),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("sequence_id", "prospect_id", name="uq_seq_contact"),
    )
    op.create_index("ix_seq_contacts_next_send", "sequence_contacts", ["next_send_at"])
    op.create_index("ix_seq_contacts_status", "sequence_contacts", ["status"])

    op.create_table(
        "email_sends",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sequence_contact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sequence_contacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("subject", sa.Text, nullable=False),
        sa.Column("body_html", sa.Text, nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), default="pending", nullable=False),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # =========================================================================
    # SIGNALS — détection automatique d'événements
    # =========================================================================
    op.create_table(
        "signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        # Types : bodacc_creation, bodacc_procedure, job_posting, news_mention,
        #         funding_round, leadership_change, website_change, inbound_form
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("signal_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("severity", sa.String(20), default="info", nullable=False),  # info/warning/critical
        sa.Column("is_read", sa.Boolean, default=False, nullable=False),
        sa.Column("metadata", postgresql.JSONB, default=dict, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_signals_prospect_id", "signals", ["prospect_id"])
    op.create_index("ix_signals_type", "signals", ["type"])
    op.create_index("ix_signals_is_read", "signals", ["is_read"])

    # =========================================================================
    # INBOUND LEADS — leads entrants via webhook (Typeform, etc.)
    # =========================================================================
    op.create_table(
        "inbound_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("token", sa.String(100), nullable=False, unique=True),  # token URL unique
        sa.Column("source_type", sa.String(50), default="webhook", nullable=False),
        sa.Column("field_mapping", postgresql.JSONB, default=dict, nullable=False),
        sa.Column("auto_enrich", sa.Boolean, default=True, nullable=False),
        sa.Column("auto_sequence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("leads_count", sa.Integer, default=0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # =========================================================================
    # ABM LISTS — listes de comptes ciblés
    # =========================================================================
    op.create_table(
        "abm_lists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("criteria", postgresql.JSONB, default=dict, nullable=False),
        sa.Column("prospects_count", sa.Integer, default=0, nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "abm_list_prospects",
        sa.Column("list_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("abm_lists.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("prospects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("score", sa.Float, nullable=True),
    )

    # =========================================================================
    # CRM SYNC CONFIGS
    # =========================================================================
    op.create_table(
        "crm_sync_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("crm_type", sa.String(30), nullable=False),  # hubspot / salesforce / pipedrive
        sa.Column("api_key_encrypted", sa.Text, nullable=True),
        sa.Column("portal_id", sa.String(50), nullable=True),
        sa.Column("field_mapping", postgresql.JSONB, default=dict, nullable=False),
        sa.Column("sync_direction", sa.String(20), default="push", nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_count", sa.Integer, default=0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("crm_sync_configs")
    op.drop_table("abm_list_prospects")
    op.drop_table("abm_lists")
    op.drop_table("inbound_sources")
    op.drop_table("signals")
    op.drop_table("email_sends")
    op.drop_table("sequence_contacts")
    op.drop_table("sequence_steps")
    op.drop_table("email_sequences")
