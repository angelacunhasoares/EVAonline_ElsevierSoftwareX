"""Create initial tables

Revision ID: 001
Revises:
Create Date: 2025-09-08

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Criar tabela eto_results
    op.create_table(
        'eto_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('elevation', sa.Float(), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('t2m_max', sa.Float(), nullable=True),
        sa.Column('t2m_min', sa.Float(), nullable=True),
        sa.Column('rh2m', sa.Float(), nullable=True),
        sa.Column('ws2m', sa.Float(), nullable=True),
        sa.Column('radiation', sa.Float(), nullable=True),
        sa.Column('precipitation', sa.Float(), nullable=True),
        sa.Column('eto', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Criar índices
    op.create_index(op.f('ix_eto_results_id'), 'eto_results', ['id'], unique=False)
    op.create_index(op.f('ix_eto_results_lat'), 'eto_results', ['lat'], unique=False)
    op.create_index(op.f('ix_eto_results_lng'), 'eto_results', ['lng'], unique=False)
    op.create_index(op.f('ix_eto_results_date'), 'eto_results', ['date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remover índices
    op.drop_index(op.f('ix_eto_results_date'), table_name='eto_results')
    op.drop_index(op.f('ix_eto_results_lng'), table_name='eto_results')
    op.drop_index(op.f('ix_eto_results_lat'), table_name='eto_results')
    op.drop_index(op.f('ix_eto_results_id'), table_name='eto_results')

    # Remover tabela
    op.drop_table('eto_results')
