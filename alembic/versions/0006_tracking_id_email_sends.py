"""add tracking_id to email_sends

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-18
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "email_sends",
        sa.Column("tracking_id", sa.String(32), nullable=True),
    )
    op.create_index("ix_email_sends_tracking_id", "email_sends", ["tracking_id"])


def downgrade() -> None:
    op.drop_index("ix_email_sends_tracking_id", "email_sends")
    op.drop_column("email_sends", "tracking_id")
