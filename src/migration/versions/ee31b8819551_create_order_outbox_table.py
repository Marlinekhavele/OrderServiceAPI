"""create order outbox table

Revision ID: ee31b8819551
Revises: 05e52ff84031
Create Date: 2025-11-18 00:13:18.103708

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ee31b8819551"
down_revision: Union[str, Sequence[str], None] = "05e52ff84031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "order_outbox",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("order_id", sa.Integer(), nullable=False, index=True),
        sa.Column("status", sa.String(), default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("order_outbox")
