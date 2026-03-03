"""Convert tenant due_date to day-of-month integer

Revision ID: 3c9a6d2e4f11
Revises: 8f1c2b7d4a10
Create Date: 2026-03-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c9a6d2e4f11'
down_revision = '8f1c2b7d4a10'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column['name'] for column in inspector.get_columns('tenants')}

    if 'due_day_of_month' not in column_names and 'due_date' in column_names:
        with op.batch_alter_table('tenants', schema=None) as batch_op:
            batch_op.add_column(sa.Column('due_day_of_month', sa.Integer(), nullable=True))

        op.execute("UPDATE tenants SET due_day_of_month = DAY(due_date) WHERE due_date IS NOT NULL")

        with op.batch_alter_table('tenants', schema=None) as batch_op:
            batch_op.drop_column('due_date')

        op.execute("ALTER TABLE tenants RENAME COLUMN due_day_of_month TO due_date")
        return

    if 'due_day_of_month' in column_names and 'due_date' not in column_names:
        op.execute("ALTER TABLE tenants RENAME COLUMN due_day_of_month TO due_date")
        return


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column['name'] for column in inspector.get_columns('tenants')}

    if 'due_date' not in column_names:
        return

    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('due_date_date', sa.Date(), nullable=True))

    op.execute(
        """
        UPDATE tenants
        SET due_date_date = STR_TO_DATE(CONCAT('2000-01-', LPAD(due_date, 2, '0')), '%Y-%m-%d')
        WHERE due_date IS NOT NULL
        """
    )

    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_column('due_date')

    op.execute("ALTER TABLE tenants RENAME COLUMN due_date_date TO due_date")
