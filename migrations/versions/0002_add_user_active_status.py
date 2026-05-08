"""add user active status

Revision ID: 0002_add_user_active_status
Revises: 0001_create_initial_tables
Create Date: 2026-05-06 00:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = "0002_add_user_active_status"
down_revision = "0001_create_initial_tables"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("is_active", server_default=None)


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_active")
