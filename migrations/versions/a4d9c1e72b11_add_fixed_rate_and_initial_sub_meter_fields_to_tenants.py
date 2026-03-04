"""Add fixed-rate and initial sub-meter fields to tenants

Revision ID: a4d9c1e72b11
Revises: 3c9a6d2e4f11
Create Date: 2026-03-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4d9c1e72b11'
down_revision = '3c9a6d2e4f11'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_fixed_power_rate', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('initial_electric_sub_meter_reading', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('is_fixed_water_rate', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('initial_water_sub_meter_reading', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_column('initial_water_sub_meter_reading')
        batch_op.drop_column('is_fixed_water_rate')
        batch_op.drop_column('initial_electric_sub_meter_reading')
        batch_op.drop_column('is_fixed_power_rate')
