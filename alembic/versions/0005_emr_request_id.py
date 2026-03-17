"""Add request_id business ID to proc_extra_material_requests

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "proc_extra_material_requests",
        sa.Column("request_id", sa.String(50), nullable=True),
    )

    # Back-fill business IDs for any existing rows
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        "SELECT id, EXTRACT(year FROM created_at) AS yr, "
        "ROW_NUMBER() OVER (PARTITION BY EXTRACT(year FROM created_at) ORDER BY created_at) AS rn "
        "FROM proc_extra_material_requests"
    )).fetchall()
    for row in rows:
        rid = f"EMR-{int(row.yr)}-{int(row.rn):03d}"
        conn.execute(
            sa.text("UPDATE proc_extra_material_requests SET request_id = :rid WHERE id = :id"),
            {"rid": rid, "id": str(row.id)},
        )

    op.create_unique_constraint(
        "uq_proc_emr_request_id", "proc_extra_material_requests", ["request_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_proc_emr_request_id", "proc_extra_material_requests", type_="unique")
    op.drop_column("proc_extra_material_requests", "request_id")
