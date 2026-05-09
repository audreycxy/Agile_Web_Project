"""add is_active to users

Revision ID: 0003_add_is_active_to_users
Revises: 0002_add_user_active_status
Create Date: 2026-05-07 00:00:00

"""

# Import Alembic and SQLAlchemy tools for database migration operations
from alembic import op
import sqlalchemy as sa


# Define Alembic revision information for this migration file
revision = "0003_add_is_active_to_users"
down_revision = "0002_add_user_active_status"
branch_labels = None
depends_on = None


def _has_column(table_name, column_name):
    # Check whether a specific column already exists in a database table
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(index_name, table_name):
    # Check whether a specific index already exists in a database table
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade():
    # Add the is_active column to the users table if it does not already exist
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

    # Create an index for the is_active column to improve account status filtering
    if not _has_index("ix_users_is_active", "users"):
        op.create_index("ix_users_is_active", "users", ["is_active"], unique=False)


def downgrade():
    # Remove the is_active index if it exists when rolling back this migration
    if _has_index("ix_users_is_active", "users"):
        op.drop_index("ix_users_is_active", table_name="users")

    # Remove the is_active column if it exists when rolling back this migration
    if _has_column("users", "is_active"):
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("is_active")