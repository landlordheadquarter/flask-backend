"""Add rate and photos to units

Revision ID: e4a2d9c7f601
Revises: d1f7a6b8c912
Create Date: 2026-03-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4a2d9c7f601'
down_revision = 'd1f7a6b8c912'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('units', sa.Column('rate', sa.Float(), nullable=True))
    op.add_column('units', sa.Column('photo_urls', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('units', 'photo_urls')
    op.drop_column('units', 'rate')
