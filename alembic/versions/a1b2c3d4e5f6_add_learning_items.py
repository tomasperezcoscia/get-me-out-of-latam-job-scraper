"""add learning_items table

Revision ID: a1b2c3d4e5f6
Revises: 993dbb59ab79
Create Date: 2026-02-11 17:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '993dbb59ab79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'learning_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skill', sa.String(100), nullable=False),
        sa.Column('detail', sa.String(500), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('is_known', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_learning_items_job_id', 'learning_items', ['job_id'])


def downgrade() -> None:
    op.drop_index('ix_learning_items_job_id', table_name='learning_items')
    op.drop_table('learning_items')
