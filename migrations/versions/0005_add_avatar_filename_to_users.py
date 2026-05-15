"""add avatar filename to users

Revision ID: 0005_add_avatar_filename_to_users
Revises: b7a2d6c4e913
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_add_avatar_filename_to_users"
down_revision = "b7a2d6c4e913"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "avatar_filename",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("users", "avatar_filename")
