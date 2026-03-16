import uuid
from datetime import datetime, timezone

from datetime import date as date_type

from sqlalchemy import String, DateTime, Integer, Numeric, Date, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProcPurchaseOrder(Base):
    __tablename__ = "proc_purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    indent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    vendor_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    site_id: Mapped[str] = mapped_column(String(100), nullable=False)
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
    dc_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dc_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    signed_dc_ismart_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ProcPoItem(Base):
    __tablename__ = "proc_po_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    item_id: Mapped[str] = mapped_column(String(50), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    landed_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)


class ProcGrn(Base):
    __tablename__ = "proc_grns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    po_number: Mapped[str] = mapped_column(String(50), nullable=False)
    requestor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    predefined_comment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comments: Mapped[str | None] = mapped_column(String, nullable=True)
    signed_dc_url: Mapped[str] = mapped_column(String(500), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class ProcGrnItem(Base):
    __tablename__ = "proc_grn_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grn_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    item_id: Mapped[str] = mapped_column(String(50), nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ordered_quantity: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    received_quantity: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    is_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)


class ProcGrnPhoto(Base):
    __tablename__ = "proc_grn_photos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grn_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False)
