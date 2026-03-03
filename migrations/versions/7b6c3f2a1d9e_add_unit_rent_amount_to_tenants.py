"""Add unit_rent_amount to tenants

Revision ID: 7b6c3f2a1d9e
Revises: 34198a4d7e3c
Create Date: 2026-03-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b6c3f2a1d9e'
down_revision = '34198a4d7e3c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('unit_rent_amount', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_column('unit_rent_amount')
