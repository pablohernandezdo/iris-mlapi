"""add prediction datetime

Revision ID: a98b337c70e4
Revises: 6630a161ae4d
Create Date: 2026-05-01 17:15:33.506395

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a98b337c70e4"
down_revision: Union[str, Sequence[str], None] = "6630a161ae4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("predictions", sa.Column("created_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("predictions", "created_at")
