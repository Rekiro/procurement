from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProcCashPurchase(Base):
    __tablename__ = "proc_cash_purchases"

    purchase_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    requestor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    site_id: Mapped[str] = mapped_column(String(100), nullable=False)
    for_the_month: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gst_no: Mapped[str | None] = mapped_column(String(15), nullable=True)
    products: Mapped[list] = mapped_column(JSONB, nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    bill_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Pending")
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
