from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Boolean, Numeric, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProcProduct(Base):
    __tablename__ = "proc_products"

    product_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subcategory: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    hsn_code: Mapped[str] = mapped_column(String(8), nullable=False)
    is_tax_exempt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gst_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    delivery_days: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    uom: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    margin_percentage: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    direct_margin_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    final_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
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


class ProcProductPriceChangeRequest(Base):
    __tablename__ = "proc_product_price_change_requests"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    product_code: Mapped[str] = mapped_column(String(20), ForeignKey("proc_products.product_code"), nullable=False)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False)
    new_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    wef_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Pending")
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
