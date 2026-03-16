"""Add dc_number, dc_date, signed_dc_ismart_url to proc_purchase_orders

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("proc_purchase_orders", sa.Column("dc_number", sa.String(50), nullable=True))
    op.add_column("proc_purchase_orders", sa.Column("dc_date", sa.Date, nullable=True))
    op.add_column("proc_purchase_orders", sa.Column("signed_dc_ismart_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("proc_purchase_orders", "signed_dc_ismart_url")
    op.drop_column("proc_purchase_orders", "dc_date")
    op.drop_column("proc_purchase_orders", "dc_number")
