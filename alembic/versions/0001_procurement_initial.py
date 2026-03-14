"""procurement initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # proc_api_logs
    op.create_table(
        "proc_api_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("path", sa.String(2048), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("user_role", sa.String(50), nullable=True),
        sa.Column("request_body", postgresql.JSONB, nullable=True),
        sa.Column("response_body", postgresql.JSONB, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=False),
        sa.Column("client_ip", sa.String(45), nullable=True),
        sa.Column("response_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_proc_api_logs_timestamp", "proc_api_logs", ["timestamp"])
    op.create_index("ix_proc_api_logs_user_email", "proc_api_logs", ["user_email"])
    op.create_index("ix_proc_api_logs_response_id", "proc_api_logs", ["response_id"])

    # proc_vendors
    op.create_table(
        "proc_vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vendor_code", sa.String(50), unique=True, nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("nature_of_business", sa.String(100), nullable=False),
        sa.Column("gl_code", sa.String(50), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="INVITED"),
        sa.Column("invite_token", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # proc_vendor_applications
    op.create_table(
        "proc_vendor_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_vendors.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_of_owner", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("designation", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("types_of_business", sa.String(100), nullable=False),
        sa.Column("address_line1", sa.Text, nullable=False),
        sa.Column("address_line2", sa.Text, nullable=True),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("pin_code", sa.String(6), nullable=False),
        sa.Column("gst_details", postgresql.JSONB, nullable=False),
        sa.Column("shop_establishment_url", sa.String(500), nullable=True),
        sa.Column("pan_url", sa.String(500), nullable=True),
        sa.Column("aadhaar_udyam_url", sa.String(500), nullable=True),
        sa.Column("msme_certificate_url", sa.String(500), nullable=True),
        sa.Column("cancelled_cheque_url", sa.String(500), nullable=True),
        sa.Column("escalation_matrix_url", sa.String(500), nullable=True),
        sa.Column("branch_office_details_url", sa.String(500), nullable=True),
        sa.Column("board_resolution_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="Pending"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(255), nullable=True),
    )

    # proc_products
    op.create_table(
        "proc_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_code", sa.String(100), unique=True, nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_vendors.id"), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("subcategory", sa.String(100), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("hsn_code", sa.String(8), nullable=False),
        sa.Column("is_tax_exempt", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("gst_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("delivery_days", sa.Integer, nullable=False),
        sa.Column("delivery_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("uom", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("margin_percentage", sa.Numeric(6, 2), nullable=True),
        sa.Column("direct_margin_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("final_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="Pending"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # proc_product_price_change_requests
    op.create_table(
        "proc_product_price_change_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_products.id"), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_vendors.id"), nullable=False),
        sa.Column("new_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("wef_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="Pending"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(255), nullable=True),
    )

    # proc_extra_material_requests
    op.create_table(
        "proc_extra_material_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("site_id", sa.String(100), nullable=False),
        sa.Column("requestor_email", sa.String(255), nullable=False),
        sa.Column("month_year", sa.Date, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_proc_emr_site_month", "proc_extra_material_requests", ["site_id", "month_year"])
    op.create_index("ix_proc_emr_status", "proc_extra_material_requests", ["status"])

    # proc_indents
    op.create_table(
        "proc_indents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tracking_no", sa.String(50), unique=True, nullable=False),
        sa.Column("requestor_email", sa.String(255), nullable=False),
        sa.Column("site_id", sa.String(100), nullable=False),
        sa.Column("for_month", sa.String(30), nullable=False),
        sa.Column("is_monthly", sa.Boolean, nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("extra_material_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_extra_material_requests.id"), nullable=True),
        sa.Column("branch_gst", sa.String(15), nullable=True),
        sa.Column("request_category", sa.String(100), nullable=True),
        sa.Column("narration", sa.Text, nullable=True),
        sa.Column("total_value", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(40), nullable=False, server_default="PENDING_PH_APPROVAL"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("rejected_by", sa.String(255), nullable=True),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # proc_indent_items
    op.create_table(
        "proc_indent_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("indent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_indents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_products.id"), nullable=True),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("size", sa.String(50), nullable=True),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
    )

    # proc_purchase_orders
    op.create_table(
        "proc_purchase_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("po_number", sa.String(50), unique=True, nullable=False),
        sa.Column("indent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_indents.id"), nullable=True),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_vendors.id"), nullable=True),
        sa.Column("site_id", sa.String(100), nullable=False),
        sa.Column("po_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_delivery_date", sa.Date, nullable=True),
        sa.Column("tat", sa.Integer, nullable=True),
        sa.Column("tat_status", sa.String(20), nullable=True),
        sa.Column("delivery_type", sa.String(20), nullable=True),
        sa.Column("courier_name", sa.String(100), nullable=True),
        sa.Column("pod_number", sa.String(100), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="Not Delivered"),
        sa.Column("date_of_delivery", sa.Date, nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("pod_image_url", sa.String(500), nullable=True),
        sa.Column("signed_pod_url", sa.String(500), nullable=True),
        sa.Column("signed_dc_url", sa.String(500), nullable=True),
        sa.Column("total_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # proc_po_items
    op.create_table(
        "proc_po_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("po_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_purchase_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.String(50), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_products.id"), nullable=True),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("landed_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
    )

    # proc_grns
    op.create_table(
        "proc_grns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("po_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_purchase_orders.id"), unique=True, nullable=False),
        sa.Column("po_number", sa.String(50), nullable=False),
        sa.Column("requestor_email", sa.String(255), nullable=False),
        sa.Column("predefined_comment", sa.String(50), nullable=True),
        sa.Column("comments", sa.Text, nullable=True),
        sa.Column("signed_dc_url", sa.String(500), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # proc_grn_items
    op.create_table(
        "proc_grn_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_grns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.String(50), nullable=False),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("ordered_quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("received_quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("is_accepted", sa.Boolean, nullable=False),
    )

    # proc_grn_photos
    op.create_table(
        "proc_grn_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("grn_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_grns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("photo_url", sa.String(500), nullable=False),
    )

    # proc_invoices
    op.create_table(
        "proc_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_id", sa.String(50), unique=True, nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_vendors.id"), nullable=True),
        sa.Column("invoice_no", sa.String(100), nullable=False),
        sa.Column("invoice_type", sa.String(20), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("bill_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("bill_url", sa.String(500), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="Pending"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(255), nullable=True),
    )

    # proc_invoice_po_links
    op.create_table(
        "proc_invoice_po_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_invoices.id"), nullable=False),
        sa.Column("po_number", sa.String(50), nullable=False),
        sa.UniqueConstraint("invoice_id", "po_number", name="uq_invoice_po"),
    )

    # proc_cash_purchases
    op.create_table(
        "proc_cash_purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("purchase_id", sa.String(50), unique=True, nullable=False),
        sa.Column("requestor_email", sa.String(255), nullable=False),
        sa.Column("site_id", sa.String(100), nullable=False),
        sa.Column("for_the_month", sa.Date, nullable=False),
        sa.Column("vendor_name", sa.String(255), nullable=True),
        sa.Column("gst_no", sa.String(15), nullable=True),
        sa.Column("products", postgresql.JSONB, nullable=False),
        sa.Column("total_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("bill_url", sa.String(500), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="Pending"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # proc_machinery_requests
    op.create_table(
        "proc_machinery_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("requisition_id", sa.String(50), unique=True, nullable=False),
        sa.Column("site_id", sa.String(100), nullable=False),
        sa.Column("site_manager_email", sa.String(255), nullable=False),
        sa.Column("justification", sa.Text, nullable=False),
        sa.Column("items", postgresql.JSONB, nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="PENDING_PH_APPROVAL"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # proc_machinery_purchase_orders
    op.create_table(
        "proc_machinery_purchase_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("po_number", sa.String(50), unique=True, nullable=False),
        sa.Column("machinery_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_machinery_requests.id"), nullable=True),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_vendors.id"), nullable=True),
        sa.Column("site_id", sa.String(100), nullable=False),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("po_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_delivery_date", sa.Date, nullable=True),
        sa.Column("tat", sa.Integer, nullable=True),
        sa.Column("tat_status", sa.String(20), nullable=True),
        sa.Column("delivery_type", sa.String(20), nullable=True),
        sa.Column("courier_name", sa.String(100), nullable=True),
        sa.Column("pod_number", sa.String(100), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="Not Delivered"),
        sa.Column("date_of_delivery", sa.Date, nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("pod_image_url", sa.String(500), nullable=True),
        sa.Column("signed_pod_url", sa.String(500), nullable=True),
        sa.Column("signed_dc_url", sa.String(500), nullable=True),
        sa.Column("items", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # proc_machinery_grns
    op.create_table(
        "proc_machinery_grns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("po_number", sa.String(50), unique=True, nullable=False),
        sa.Column("requestor_email", sa.String(255), nullable=False),
        sa.Column("comments", sa.Text, nullable=True),
        sa.Column("signed_dc_url", sa.String(500), nullable=False),
        sa.Column("asset_condition_proof_url", sa.String(500), nullable=False),
        sa.Column("packaging_images", postgresql.JSONB, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # proc_uniform_requests
    op.create_table(
        "proc_uniform_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", sa.String(50), unique=True, nullable=False),
        sa.Column("employee_code", sa.String(50), nullable=False),
        sa.Column("employee_name", sa.String(255), nullable=False),
        sa.Column("designation", sa.String(100), nullable=False),
        sa.Column("site", sa.String(100), nullable=False),
        sa.Column("client", sa.String(100), nullable=True),
        sa.Column("issue_type", sa.String(20), nullable=False),
        sa.Column("replacing_employee_code", sa.String(50), nullable=True),
        sa.Column("justification", sa.Text, nullable=True),
        sa.Column("is_early_replacement", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("items", postgresql.JSONB, nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="PENDING_PH_APPROVAL"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # proc_uniform_purchase_orders
    op.create_table(
        "proc_uniform_purchase_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("po_number", sa.String(50), unique=True, nullable=False),
        sa.Column("uniform_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_uniform_requests.id"), nullable=True),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proc_vendors.id"), nullable=True),
        sa.Column("employee_name", sa.String(255), nullable=False),
        sa.Column("employee_code", sa.String(50), nullable=False),
        sa.Column("site_name", sa.String(255), nullable=False),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("po_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_delivery_date", sa.Date, nullable=True),
        sa.Column("tat", sa.Integer, nullable=True),
        sa.Column("tat_status", sa.String(20), nullable=True),
        sa.Column("delivery_type", sa.String(20), nullable=True),
        sa.Column("courier_name", sa.String(100), nullable=True),
        sa.Column("pod_number", sa.String(100), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="Not Delivered"),
        sa.Column("date_of_delivery", sa.Date, nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("pod_image_url", sa.String(500), nullable=True),
        sa.Column("signed_pod_url", sa.String(500), nullable=True),
        sa.Column("signed_dc_url", sa.String(500), nullable=True),
        sa.Column("items", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # proc_notifications
    op.create_table(
        "proc_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("link", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_proc_notifications_user_email", "proc_notifications", ["user_email"])
    op.create_index("ix_proc_notifications_is_read", "proc_notifications", ["is_read"])


def downgrade() -> None:
    op.drop_table("proc_notifications")
    op.drop_table("proc_uniform_purchase_orders")
    op.drop_table("proc_uniform_requests")
    op.drop_table("proc_machinery_grns")
    op.drop_table("proc_machinery_purchase_orders")
    op.drop_table("proc_machinery_requests")
    op.drop_table("proc_cash_purchases")
    op.drop_table("proc_invoice_po_links")
    op.drop_table("proc_invoices")
    op.drop_table("proc_grn_photos")
    op.drop_table("proc_grn_items")
    op.drop_table("proc_grns")
    op.drop_table("proc_po_items")
    op.drop_table("proc_purchase_orders")
    op.drop_table("proc_indent_items")
    op.drop_table("proc_indents")
    op.drop_table("proc_extra_material_requests")
    op.drop_table("proc_product_price_change_requests")
    op.drop_table("proc_products")
    op.drop_table("proc_vendor_applications")
    op.drop_table("proc_vendors")
    op.drop_table("proc_api_logs")
