"""Add meter usage and rate fields to billing_periods

Revision ID: f3b9d4a2c118
Revises: e21c6a9f4b33
Create Date: 2026-03-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3b9d4a2c118'
down_revision = 'e21c6a9f4b33'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('billing_periods', sa.Column('previous_electric_sub_meter_reading', sa.Float(), nullable=True))
    op.add_column('billing_periods', sa.Column('used_electric_kwh', sa.Float(), nullable=True))
    op.add_column('billing_periods', sa.Column('electric_rate_per_kwh', sa.Float(), nullable=True))
    op.add_column('billing_periods', sa.Column('previous_water_sub_meter_reading', sa.Float(), nullable=True))
    op.add_column('billing_periods', sa.Column('used_water_cubic_meter', sa.Float(), nullable=True))
    op.add_column('billing_periods', sa.Column('water_rate_per_cubic_meter', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('billing_periods', 'water_rate_per_cubic_meter')
    op.drop_column('billing_periods', 'used_water_cubic_meter')
    op.drop_column('billing_periods', 'previous_water_sub_meter_reading')
    op.drop_column('billing_periods', 'electric_rate_per_kwh')
    op.drop_column('billing_periods', 'used_electric_kwh')
    op.drop_column('billing_periods', 'previous_electric_sub_meter_reading')
