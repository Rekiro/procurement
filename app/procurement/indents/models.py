import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Boolean, Numeric, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProcIndent(Base):
    __tablename__ = "proc_indents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    requestor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    site_id: Mapped[str] = mapped_column(String(100), nullable=False)
    for_month: Mapped[str] = mapped_column(String(30), nullable=False)
    is_monthly: Mapped[bool] = mapped_column(Boolean, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    emr_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("proc_extra_material_requests.emr_id"), nullable=True)
    branch_gst: Mapped[str | None] = mapped_column(String(15), nullable=True)
    request_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    narration: Mapped[str | None] = mapped_column(String, nullable=True)
    total_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="PENDING_PH_APPROVAL")
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    rejected_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ProcIndentItem(Base):
    __tablename__ = "proc_indent_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
