"""backfill seeded users as verified

Revision ID: 9d7a4c2b1f0e
Revises: 52016dd399f3
Create Date: 2026-05-10 23:58:00
"""

from alembic import op
import sqlalchemy as sa


revision = "9d7a4c2b1f0e"
down_revision = "52016dd399f3"
branch_labels = None
depends_on = None


SEED_EMAILS = ("admin@example.com", "player@example.com")


def upgrade():
    op.execute(
        sa.text(
            """
            UPDATE users
            SET is_active = 1,
                email_verified = 1,
                email_verification_token = NULL
            WHERE email IN :seed_emails
            """
        ).bindparams(sa.bindparam("seed_emails", expanding=True, value=SEED_EMAILS))
    )


def downgrade():
    op.execute(
        sa.text(
            """
            UPDATE users
            SET email_verified = 0
            WHERE email IN :seed_emails
            """
        ).bindparams(sa.bindparam("seed_emails", expanding=True, value=SEED_EMAILS))
    )
