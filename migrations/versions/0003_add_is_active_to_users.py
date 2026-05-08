"""add is_active to users

Revision ID: 0003_add_is_active_to_users
Revises: 0002_add_user_active_status
Create Date: 2026-05-07 00:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = "0003_add_is_active_to_users"
down_revision = "0002_add_user_active_status"
branch_labels = None
depends_on = None


def _has_column(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(index_name, table_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade():
    if not _has_column("users", "is_active"):
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "is_active",
                    sa.Boolean(),
                    nullable=False,
                    server_default="1",
                )
            )

    if not _has_index("ix_users_is_active", "users"):
        op.create_index("ix_users_is_active", "users", ["is_active"], unique=False)


def downgrade():
    if _has_index("ix_users_is_active", "users"):
        op.drop_index("ix_users_is_active", table_name="users")

    if _has_column("users", "is_active"):
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("is_active")
