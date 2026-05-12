"""merge migration heads

Revision ID: 52016dd399f3
Revises: 0004_add_email_verification_to_users, 5b2ffc77b36e
Create Date: 2026-05-10 16:17:16.607538

"""
from alembic import op
import sqlalchemy as sa


revision = '52016dd399f3'
down_revision = ('0004_add_email_verification_to_users', '5b2ffc77b36e')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
