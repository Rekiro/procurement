from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProcVendor(Base):
    __tablename__ = "proc_vendors"

    vendor_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    nature_of_business: Mapped[str] = mapped_column(String(100), nullable=False)
    gl_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="INVITED")
    invite_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ProcVendorApplication(Base):
    __tablename__ = "proc_vendor_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("proc_vendors.vendor_code"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_of_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    types_of_business: Mapped[str] = mapped_column(String(100), nullable=False)
    address_line1: Mapped[str] = mapped_column(String, nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    pin_code: Mapped[str] = mapped_column(String(6), nullable=False)
    gst_details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    shop_establishment_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pan_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    aadhaar_udyam_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    msme_certificate_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cancelled_cheque_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    escalation_matrix_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    branch_office_details_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    board_resolution_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Pending")
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
