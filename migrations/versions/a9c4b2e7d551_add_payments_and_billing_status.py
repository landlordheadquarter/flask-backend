"""Add payments table and billing status fields

Revision ID: a9c4b2e7d551
Revises: f3b9d4a2c118
Create Date: 2026-03-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9c4b2e7d551'
down_revision = 'f3b9d4a2c118'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('billing_periods', sa.Column('paid_amount', sa.Float(), nullable=False, server_default='0'))
    op.add_column('billing_periods', sa.Column('status', sa.String(length=30), nullable=False, server_default='issued'))

    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('billing_period_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('reference_no', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['billing_period_id'], ['billing_periods.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('payments')
    op.drop_column('billing_periods', 'status')
    op.drop_column('billing_periods', 'paid_amount')
