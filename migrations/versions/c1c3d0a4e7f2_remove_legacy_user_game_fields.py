"""remove legacy game progress fields from users

Revision ID: c1c3d0a4e7f2
Revises: b7a2d6c4e913
Create Date: 2026-05-17 14:45:00
"""

from alembic import op
import sqlalchemy as sa


revision = "c1c3d0a4e7f2"
down_revision = "b7a2d6c4e913"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("progress_percent")
        batch_op.drop_column("clicks_remaining")
        batch_op.drop_column("highest_type")
        batch_op.drop_column("current_type")
        batch_op.drop_column("current_infinity_level")
        batch_op.drop_column("points")


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("points", sa.Integer(), server_default="0", nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "current_infinity_level",
                sa.Integer(),
                server_default="0",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "current_type",
                sa.String(length=50),
                server_default="standard",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "highest_type",
                sa.String(length=50),
                server_default="standard",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("clicks_remaining", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "progress_percent",
                sa.Integer(),
                server_default="0",
                nullable=False,
            )
        )
