"""add soft delete fields to users

Revision ID: b7a2d6c4e913
Revises: 1122b93fa521
Create Date: 2026-05-12 15:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "b7a2d6c4e913"
down_revision = "1122b93fa521"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_deleted", sa.Boolean(), server_default="0", nullable=False)
        )
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_users_is_deleted", ["is_deleted"], unique=False)


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_is_deleted")
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("is_deleted")
