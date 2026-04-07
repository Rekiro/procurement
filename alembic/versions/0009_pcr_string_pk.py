"""Price change requests: change id from SERIAL integer to VARCHAR string (PROD-EDIT-{timestamp_ms})

Revision ID: 0009
Revises: 0008
Create Date: 2026-03-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Truncate existing test data — the integer PK is not compatible with the new string PK format.
    # In dev this table has no meaningful data; in production this migration should be run before any real data is inserted.
    op.execute("TRUNCATE TABLE proc_product_price_change_requests")

    # Drop the integer primary key and replace with a VARCHAR primary key
    # Step 1: Drop existing PK constraint
    op.drop_constraint("proc_product_price_change_requests_pkey", "proc_product_price_change_requests", type_="primary")

    # Step 2: Drop the old integer id column
    op.drop_column("proc_product_price_change_requests", "id")

    # Step 3: Add new VARCHAR id column as primary key
    op.add_column(
        "proc_product_price_change_requests",
        sa.Column("id", sa.String(50), nullable=False),
    )
    op.create_primary_key("proc_product_price_change_requests_pkey", "proc_product_price_change_requests", ["id"])


def downgrade() -> None:
    op.drop_constraint("proc_product_price_change_requests_pkey", "proc_product_price_change_requests", type_="primary")
    op.drop_column("proc_product_price_change_requests", "id")
    op.add_column(
        "proc_product_price_change_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
    )
    op.execute("CREATE SEQUENCE IF NOT EXISTS proc_product_price_change_requests_id_seq")
    op.execute("ALTER TABLE proc_product_price_change_requests ALTER COLUMN id SET DEFAULT nextval('proc_product_price_change_requests_id_seq')")
    op.create_primary_key("proc_product_price_change_requests_pkey", "proc_product_price_change_requests", ["id"])
