import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProcInvoice(Base):
    __tablename__ = "proc_invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    vendor_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    invoice_no: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_type: Mapped[str] = mapped_column(String(20), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    bill_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    bill_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Pending")
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ProcInvoicePoLink(Base):
    __tablename__ = "proc_invoice_po_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    po_number: Mapped[str] = mapped_column(String(50), nullable=False)
