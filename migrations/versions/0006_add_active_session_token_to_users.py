"""add active session token to users

Revision ID: 0006_add_active_session_token_to_users
Revises: 0005_add_avatar_filename_to_users
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_add_active_session_token_to_users"
down_revision = "0005_add_avatar_filename_to_users"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "active_session_token",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("users", "active_session_token")
