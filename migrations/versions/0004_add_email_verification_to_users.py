"""add email verification to users

Revision ID: 0004_add_email_verification_to_users
Revises: 0003_add_is_active_to_users
Create Date: 2026-05-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_add_email_verification_to_users"
down_revision = "0003_add_is_active_to_users"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verification_token",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_users_email_verified",
        "users",
        ["email_verified"],
        unique=False,
    )
    op.create_index(
        "ix_users_email_verification_token",
        "users",
        ["email_verification_token"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_users_email_verification_token", table_name="users")
    op.drop_index("ix_users_email_verified", table_name="users")
    op.drop_column("users", "email_verification_token")
    op.drop_column("users", "email_verified")