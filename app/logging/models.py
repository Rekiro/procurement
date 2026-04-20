"""Shared `api_logs` table — owned by the Account Master service.

Procurement re-declares the model here for ORM use, but never creates,
alters, or drops the table itself. The migration is in
accountMaster/alembic/versions/0001_account_master_initial.py and the
table is excluded from procurement's autogenerate via env.py's
`include_object` filter.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, BigInteger, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.shared.timezone import IST


class ApiLog(Base):
    __tablename__ = "api_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    module: Mapped[str] = mapped_column(String(30), nullable=False)
    request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(IST)
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    request_body: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_body: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_api_logs_module_timestamp", "module", "timestamp"),
        Index("ix_api_logs_user_timestamp", "user_id", "timestamp"),
        Index("ix_api_logs_path_status", "path", "status_code"),
        {"schema": "shared"},
    )
