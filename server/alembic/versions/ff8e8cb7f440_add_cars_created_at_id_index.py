"""add cars created_at id index

Revision ID: ff8e8cb7f440
Revises: 2e850f6f1ce6
Create Date: 2026-11-03 12:18:00.131009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff8e8cb7f440'
down_revision: Union[str, None] = '2e850f6f1ce6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_cars_created_at_id', 'cars', ['created_at', 'id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_cars_created_at_id', table_name='cars')
