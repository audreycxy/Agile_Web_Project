"""create initial tables

Revision ID: 0001_create_initial_tables
Revises:
Create Date: 2026-04-15 00:00:00

"""

# Import Alembic and SQLAlchemy tools for defining database migrations
from alembic import op
import sqlalchemy as sa


# Define Alembic revision information for this migration file
revision = "0001_create_initial_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create the initial database tables for users and game results

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('admin', 'player')", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )

    # Add indexes to improve user lookup by email and role
    op.create_index(
        op.f("ix_users_email"),
        "users",
        ["email"],
        unique=True,
        if_not_exists=True,
    )
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False, if_not_exists=True)

    # Create the game results table and link each result to a user account
    op.create_table(
        "game_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )

    # Add an index for faster searching of game results by user ID
    op.create_index(
        op.f("ix_game_results_user_id"),
        "game_results",
        ["user_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade():
    # Remove the initial tables and indexes when rolling back this migration

    op.drop_index(op.f("ix_game_results_user_id"), table_name="game_results")
    op.drop_table("game_results")
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")