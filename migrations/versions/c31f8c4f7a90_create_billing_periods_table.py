"""Create billing_periods table

Revision ID: c31f8c4f7a90
Revises: b87ea35df124
Create Date: 2026-03-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c31f8c4f7a90'
down_revision = 'b87ea35df124'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'billing_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('from_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('monthly_rent_amount', sa.Float(), nullable=False),
        sa.Column('electric_charge_amount', sa.Float(), nullable=True),
        sa.Column('water_charge_amount', sa.Float(), nullable=True),
        sa.Column('current_electric_sub_meter_reading', sa.Float(), nullable=True),
        sa.Column('current_water_sub_meter_reading', sa.Float(), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('billing_periods')
