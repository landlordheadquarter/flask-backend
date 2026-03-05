"""Add contact number to users

Revision ID: a7c9d2e4f115
Revises: f2d7a1b9e6c4
Create Date: 2026-03-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7c9d2e4f115'
down_revision = 'f2d7a1b9e6c4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('contact_no', sa.String(length=30), nullable=True))


def downgrade():
    op.drop_column('users', 'contact_no')
