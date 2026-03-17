"""Rename EMR columns to short names

- proc_extra_material_requests: extra_material_request_id → emr_id
- proc_indents: extra_material_request_id → emr_id (FK updated)

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop FK from proc_indents before renaming PK
    op.drop_constraint("fk_proc_indents_emr", "proc_indents", type_="foreignkey")

    # Rename PK column on proc_extra_material_requests
    op.alter_column(
        "proc_extra_material_requests", "extra_material_request_id",
        new_column_name="emr_id"
    )

    # Rename FK column on proc_indents
    op.alter_column(
        "proc_indents", "extra_material_request_id",
        new_column_name="emr_id"
    )

    # Re-create FK with new column names
    op.create_foreign_key(
        "fk_proc_indents_emr",
        "proc_indents", "proc_extra_material_requests",
        ["emr_id"], ["emr_id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_proc_indents_emr", "proc_indents", type_="foreignkey")
    op.alter_column("proc_indents", "emr_id", new_column_name="extra_material_request_id")
    op.alter_column(
        "proc_extra_material_requests", "emr_id",
        new_column_name="extra_material_request_id"
    )
    op.create_foreign_key(
        "fk_proc_indents_emr",
        "proc_indents", "proc_extra_material_requests",
        ["extra_material_request_id"], ["extra_material_request_id"]
    )
