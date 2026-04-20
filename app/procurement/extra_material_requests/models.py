from datetime import datetime

from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.shared.timezone import IST


class ProcExtraMaterialRequest(Base):
    __tablename__ = "proc_extra_material_requests"

    emr_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    site_id: Mapped[str] = mapped_column(String(100), nullable=False)
    requestor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    month_year: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(IST)
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_proc_emr_site_month", "site_id", "month_year"),
        Index("ix_proc_emr_status", "status"),
    )
