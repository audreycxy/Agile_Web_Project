"""add user active status

Revision ID: 0002_add_user_active_status
Revises: 0001_create_initial_tables
Create Date: 2026-05-06 00:00:00

"""

# Import Alembic and SQLAlchemy tools for modifying the database schema
from alembic import op
import sqlalchemy as sa


# Define Alembic revision information for this migration file
revision = "0002_add_user_active_status"
down_revision = "0001_create_initial_tables"
branch_labels = None
depends_on = None


def upgrade():
    # Add an is_active column to the users table
    # Existing users are set to active by default during the migration
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )

    # Remove the database-level default after existing records have been updated
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("is_active", server_default=None)


def downgrade():
    # Remove the is_active column when rolling back this migration
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_active")