"""Add tenant portal credentials

Revision ID: d1f7a6b8c912
Revises: c3e8f1a9b204
Create Date: 2026-03-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1f7a6b8c912'
down_revision = 'c3e8f1a9b204'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tenants', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('password', sa.String(length=255), nullable=True))
    op.create_unique_constraint('uq_tenants_email', 'tenants', ['email'])


def downgrade():
    op.drop_constraint('uq_tenants_email', 'tenants', type_='unique')
    op.drop_column('tenants', 'password')
    op.drop_column('tenants', 'email')
