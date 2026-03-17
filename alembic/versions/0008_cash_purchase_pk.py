"""Cash purchases: remove UUID id, make purchase_id PK

- Drop UUID id column (was primary key)
- Drop unique constraint on purchase_id
- Make purchase_id the primary key

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the UUID primary key constraint + id column
    op.drop_constraint("proc_cash_purchases_pkey", "proc_cash_purchases", type_="primary")
    op.drop_column("proc_cash_purchases", "id")

    # Drop unique constraint on purchase_id (will be replaced by PK)
    op.drop_constraint("proc_cash_purchases_purchase_id_key", "proc_cash_purchases", type_="unique")

    # Make purchase_id the primary key
    op.create_primary_key("proc_cash_purchases_pkey", "proc_cash_purchases", ["purchase_id"])


def downgrade() -> None:
    op.drop_constraint("proc_cash_purchases_pkey", "proc_cash_purchases", type_="primary")
    op.add_column(
        "proc_cash_purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
    )
    op.create_primary_key("proc_cash_purchases_pkey", "proc_cash_purchases", ["id"])
    op.create_unique_constraint("proc_cash_purchases_purchase_id_key", "proc_cash_purchases", ["purchase_id"])
