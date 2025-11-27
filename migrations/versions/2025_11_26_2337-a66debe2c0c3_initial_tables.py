"""initial tables

Revision ID: a66debe2c0c3
Revises: 4f7915bf1804
Create Date: 2025-11-26 23:37:38.645922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a66debe2c0c3'
down_revision: Union[str, Sequence[str], None] = '4f7915bf1804'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
