"""Replace UUID PK with business ID on proc_extra_material_requests

- Drop UUID `id` primary key
- Rename `request_id` → `extra_material_request_id`, make it the PK
- Drop UUID `extra_material_request_id` column from proc_indents
- Add VARCHAR(50) `extra_material_request_id` FK column to proc_indents

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Drop FK from proc_indents that references old UUID PK ────────────
    # Check if it exists before dropping (may or may not be present)
    has_fk = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.table_constraints "
        "WHERE constraint_name = 'proc_indents_extra_material_request_id_fkey' "
        "AND table_name = 'proc_indents'"
    )).fetchone()
    if has_fk:
        op.drop_constraint(
            "proc_indents_extra_material_request_id_fkey", "proc_indents", type_="foreignkey"
        )

    # ── 2. Drop old UUID extra_material_request_id from proc_indents ────────
    op.drop_column("proc_indents", "extra_material_request_id")

    # ── 3. proc_extra_material_requests: swap UUID PK → business ID PK ─────

    # Drop unique constraint added in 0005
    op.drop_constraint(
        "uq_proc_emr_request_id", "proc_extra_material_requests", type_="unique"
    )

    # Make request_id NOT NULL (all rows were backfilled in 0005)
    op.alter_column(
        "proc_extra_material_requests", "request_id",
        existing_type=sa.String(50), nullable=False
    )

    # Drop UUID primary key constraint (no dependents remain now)
    op.drop_constraint(
        "proc_extra_material_requests_pkey", "proc_extra_material_requests", type_="primary"
    )
    op.drop_column("proc_extra_material_requests", "id")

    # Rename request_id → extra_material_request_id
    op.alter_column(
        "proc_extra_material_requests", "request_id",
        new_column_name="extra_material_request_id"
    )

    # Make extra_material_request_id the new PK
    op.create_primary_key(
        "proc_extra_material_requests_pkey",
        "proc_extra_material_requests",
        ["extra_material_request_id"]
    )

    # ── 4. Add new VARCHAR FK column to proc_indents ─────────────────────────
    op.add_column(
        "proc_indents",
        sa.Column("extra_material_request_id", sa.String(50), nullable=True)
    )
    op.create_foreign_key(
        "fk_proc_indents_emr",
        "proc_indents", "proc_extra_material_requests",
        ["extra_material_request_id"], ["extra_material_request_id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_proc_indents_emr", "proc_indents", type_="foreignkey")
    op.drop_column("proc_indents", "extra_material_request_id")

    op.drop_constraint(
        "proc_extra_material_requests_pkey", "proc_extra_material_requests", type_="primary"
    )
    op.alter_column(
        "proc_extra_material_requests", "extra_material_request_id",
        new_column_name="request_id"
    )
    op.add_column(
        "proc_extra_material_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()"))
    )
    op.create_primary_key(
        "proc_extra_material_requests_pkey",
        "proc_extra_material_requests", ["id"]
    )
    op.create_unique_constraint(
        "uq_proc_emr_request_id", "proc_extra_material_requests", ["request_id"]
    )
    op.add_column(
        "proc_indents",
        sa.Column("extra_material_request_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
