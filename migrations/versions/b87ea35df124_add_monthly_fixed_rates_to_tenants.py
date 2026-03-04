"""Add monthly fixed electric and water rates to tenants

Revision ID: b87ea35df124
Revises: a4d9c1e72b11
Create Date: 2026-03-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b87ea35df124'
down_revision = 'a4d9c1e72b11'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('monthly_fixed_power_rate', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('monthly_fixed_water_rate', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_column('monthly_fixed_water_rate')
        batch_op.drop_column('monthly_fixed_power_rate')
