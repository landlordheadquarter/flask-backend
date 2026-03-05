"""Add user profile fields

Revision ID: f2d7a1b9e6c4
Revises: e4a2d9c7f601
Create Date: 2026-03-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2d7a1b9e6c4'
down_revision = 'e4a2d9c7f601'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('address', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('profile_photo_url', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('users', 'longitude')
    op.drop_column('users', 'latitude')
    op.drop_column('users', 'profile_photo_url')
    op.drop_column('users', 'address')
