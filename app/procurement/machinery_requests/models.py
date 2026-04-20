import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.shared.timezone import IST


class ProcMachineryRequest(Base):
    __tablename__ = "proc_machinery_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requisition_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    site_id: Mapped[str] = mapped_column(String(100), nullable=False)
    site_manager_email: Mapped[str] = mapped_column(String(255), nullable=False)
    justification: Mapped[str] = mapped_column(String, nullable=False)
    items: Mapped[list] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="PENDING_PH_APPROVAL")
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(IST)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(IST),
        onupdate=lambda: datetime.now(IST),
    )


class ProcMachineryPurchaseOrder(Base):
    __tablename__ = "proc_machinery_purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    machinery_request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    vendor_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    site_id: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    po_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tat: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tat_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    delivery_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    courier_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pod_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="Not Delivered")
    date_of_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    pod_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    signed_pod_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    signed_dc_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    items: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(IST)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(IST),
        onupdate=lambda: datetime.now(IST),
    )


class ProcMachineryGrn(Base):
    __tablename__ = "proc_machinery_grns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    requestor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    comments: Mapped[str | None] = mapped_column(String, nullable=True)
    signed_dc_url: Mapped[str] = mapped_column(String(500), nullable=False)
    asset_condition_proof_url: Mapped[str] = mapped_column(String(500), nullable=False)
    packaging_images: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(IST)
    )
