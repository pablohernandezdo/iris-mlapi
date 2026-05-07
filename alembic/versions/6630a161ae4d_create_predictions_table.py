"""create predictions table

Revision ID: 6630a161ae4d
Revises:
Create Date: 2026-05-01 17:04:57.885353

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6630a161ae4d"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sepal_length", sa.Float(), nullable=False),
        sa.Column("sepal_width", sa.Float(), nullable=False),
        sa.Column("petal_length", sa.Float(), nullable=False),
        sa.Column("petal_width", sa.Float(), nullable=False),
        sa.Column("predicted_class", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("predictions")
