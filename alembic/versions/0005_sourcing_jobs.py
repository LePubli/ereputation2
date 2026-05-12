"""add sourcing_jobs table

Revision ID: 0005_sourcing_jobs
Revises: 0004_sequencer_signals_inbound_abm
Create Date: 2025-01-01 00:00:00
"""
from alembic import op

revision = '0005_sourcing_jobs'
down_revision = None   # ← on va corriger cette ligne
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS sourcing_jobs (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name         VARCHAR(255) NOT NULL,
            source       VARCHAR(64) NOT NULL,
            config       JSONB DEFAULT '{}',
            status       VARCHAR(32) NOT NULL DEFAULT 'pending',
            progress     INTEGER DEFAULT 0,
            found_count  INTEGER DEFAULT 0,
            new_count    INTEGER DEFAULT 0,
            error        TEXT,
            created_by   UUID,
            created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE
        );
        CREATE INDEX IF NOT EXISTS idx_sourcing_jobs_status ON sourcing_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_sourcing_jobs_created ON sourcing_jobs(created_at DESC);
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS sourcing_jobs CASCADE;")
