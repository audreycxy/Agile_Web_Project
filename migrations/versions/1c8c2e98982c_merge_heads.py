"""merge heads

Revision ID: 1c8c2e98982c
Revises: 9e3602ddd734, 0004_add_email_verification_to_users
Create Date: 2026-05-10 21:29:32.742886

"""
from alembic import op
import sqlalchemy as sa


revision = '1c8c2e98982c'
down_revision = ('9e3602ddd734', '0004_add_email_verification_to_users')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
