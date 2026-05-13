"""merge migration heads

Revision ID: 1122b93fa521
Revises: 1c8c2e98982c, 9d7a4c2b1f0e
Create Date: 2026-05-12 10:47:05.350299

"""
from alembic import op
import sqlalchemy as sa


revision = '1122b93fa521'
down_revision = ('1c8c2e98982c', '9d7a4c2b1f0e')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
