"""enforce_created_at_not_null

Revision ID: a884fd4fd769
Revises: a98b337c70e4
Create Date: 2026-05-06 23:16:44.608972

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a884fd4fd769"
down_revision: Union[str, Sequence[str], None] = "a98b337c70e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE predictions SET created_at = GETUTCDATE() WHERE created_at IS NULL"
    )
    op.alter_column(
        "predictions",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False,
        server_default=sa.text("GETUTCDATE()"),
    )


def downgrade() -> None:
    op.alter_column(
        "predictions",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=True,
        server_default=None,
    )
