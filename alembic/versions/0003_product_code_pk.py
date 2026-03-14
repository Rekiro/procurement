"""Replace product UUID PK with product_code string PK

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-14

Switches proc_products from UUID id to product_code string PK.
Updates proc_product_price_change_requests to int PK + product_code FK.
Updates proc_indent_items and proc_po_items: product_id UUID -> product_code string.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 1. Drop FK constraints from dependent tables ---

    # proc_product_price_change_requests -> proc_products.id
    op.drop_constraint(
        "proc_product_price_change_requests_product_id_fkey",
        "proc_product_price_change_requests",
        type_="foreignkey",
    )

    # proc_indent_items -> proc_products.id
    op.drop_constraint(
        "proc_indent_items_product_id_fkey",
        "proc_indent_items",
        type_="foreignkey",
    )

    # proc_po_items -> proc_products.id
    op.drop_constraint(
        "proc_po_items_product_id_fkey",
        "proc_po_items",
        type_="foreignkey",
    )

    # --- 2. Fix proc_products: drop UUID id PK, make product_code the PK ---

    # Drop PK constraint on id
    op.drop_constraint("proc_products_pkey", "proc_products", type_="primary")

    # Drop the UUID id column
    op.drop_column("proc_products", "id")

    # Drop unique constraint on product_code (it will become PK which is already unique)
    op.drop_constraint("proc_products_product_code_key", "proc_products", type_="unique")

    # Alter product_code to VARCHAR(20) to match model
    op.alter_column("proc_products", "product_code", type_=sa.String(20), existing_nullable=False)

    # Add PK on product_code
    op.create_primary_key("proc_products_pkey", "proc_products", ["product_code"])

    # --- 3. Fix proc_product_price_change_requests ---

    # Drop PK + id UUID column
    op.drop_constraint("proc_product_price_change_requests_pkey", "proc_product_price_change_requests", type_="primary")
    op.drop_column("proc_product_price_change_requests", "id")

    # Add SERIAL id column as PK
    op.add_column(
        "proc_product_price_change_requests",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    )
    op.create_primary_key(
        "proc_product_price_change_requests_pkey",
        "proc_product_price_change_requests",
        ["id"],
    )

    # Drop product_id UUID column
    op.drop_column("proc_product_price_change_requests", "product_id")

    # Add product_code column + FK
    op.add_column(
        "proc_product_price_change_requests",
        sa.Column("product_code", sa.String(20), nullable=True),
    )
    op.create_foreign_key(
        "proc_product_price_change_requests_product_code_fkey",
        "proc_product_price_change_requests",
        "proc_products",
        ["product_code"],
        ["product_code"],
    )

    # --- 4. Fix proc_indent_items ---

    # Drop product_id UUID column
    op.drop_column("proc_indent_items", "product_id")

    # Add product_code column + FK
    op.add_column(
        "proc_indent_items",
        sa.Column("product_code", sa.String(20), nullable=True),
    )
    op.create_foreign_key(
        "proc_indent_items_product_code_fkey",
        "proc_indent_items",
        "proc_products",
        ["product_code"],
        ["product_code"],
    )

    # --- 5. Fix proc_po_items ---

    # Drop product_id UUID column
    op.drop_column("proc_po_items", "product_id")

    # Add product_code column + FK
    op.add_column(
        "proc_po_items",
        sa.Column("product_code", sa.String(20), nullable=True),
    )
    op.create_foreign_key(
        "proc_po_items_product_code_fkey",
        "proc_po_items",
        "proc_products",
        ["product_code"],
        ["product_code"],
    )


def downgrade() -> None:
    # Not implementing full downgrade — this is a dev migration
    pass
