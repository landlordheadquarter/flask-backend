"""Phase 2 bulk billing, overdue fields, and notifications

Revision ID: b7f4e2d1c903
Revises: a9c4b2e7d551
Create Date: 2026-03-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7f4e2d1c903'
down_revision = 'a9c4b2e7d551'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('billing_periods', sa.Column('due_date', sa.Date(), nullable=True))
    op.add_column('billing_periods', sa.Column('late_fee_amount', sa.Float(), nullable=False, server_default='0'))

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('billing_period_id', sa.Integer(), nullable=True),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('message', sa.String(length=255), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['billing_period_id'], ['billing_periods.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('notifications')
    op.drop_column('billing_periods', 'late_fee_amount')
    op.drop_column('billing_periods', 'due_date')
