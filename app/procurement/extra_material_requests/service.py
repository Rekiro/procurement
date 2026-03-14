import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.extra_material_requests.models import ProcExtraMaterialRequest
from app.procurement.extra_material_requests.schemas import (
    ExtraMaterialRequestCreate,
    ApproveEMRRequest,
    RejectEMRRequest,
)


async def get_status(db: AsyncSession, requestor_email: str, site_id: str) -> dict:
    """Check if requestor has an approved EMR for the current month at their site."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ProcExtraMaterialRequest)
        .where(ProcExtraMaterialRequest.requestor_email == requestor_email)
        .where(ProcExtraMaterialRequest.site_id == site_id)
        .where(ProcExtraMaterialRequest.status == "approved")
        .where(extract("year", ProcExtraMaterialRequest.month_year) == now.year)
        .where(extract("month", ProcExtraMaterialRequest.month_year) == now.month)
    )
    approved = result.scalars().first()
    return {
        "hasApproval": approved is not None,
        "requestId": str(approved.id) if approved else None,
        "month": now.strftime("%Y-%m"),
        "siteId": site_id,
    }


async def create_request(
    db: AsyncSession, data: ExtraMaterialRequestCreate, user_email: str
) -> ProcExtraMaterialRequest:
    try:
        month_year_dt = datetime.strptime(data.monthYear + "-01", "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="monthYear must be in format YYYY-MM (e.g. 2026-03)",
        )

    # One pending/approved EMR per requestor+site per month
    existing = await db.execute(
        select(ProcExtraMaterialRequest)
        .where(ProcExtraMaterialRequest.requestor_email == user_email)
        .where(ProcExtraMaterialRequest.site_id == data.siteId)
        .where(ProcExtraMaterialRequest.status.in_(["pending", "approved"]))
        .where(extract("year", ProcExtraMaterialRequest.month_year) == month_year_dt.year)
        .where(extract("month", ProcExtraMaterialRequest.month_year) == month_year_dt.month)
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active EMR already exists for this site and month",
        )

    emr = ProcExtraMaterialRequest(
        site_id=data.siteId,
        requestor_email=user_email,
        month_year=month_year_dt,
        reason=data.reason,
        status="pending",
    )
    db.add(emr)
    await db.commit()
    await db.refresh(emr)
    return emr


async def list_requests(
    db: AsyncSession, status_filter: str | None = None
) -> list[ProcExtraMaterialRequest]:
    q = select(ProcExtraMaterialRequest).order_by(
        ProcExtraMaterialRequest.created_at.desc()
    )
    if status_filter:
        q = q.where(ProcExtraMaterialRequest.status == status_filter)
    result = await db.execute(q)
    return list(result.scalars().all())


async def approve_request(
    db: AsyncSession, data: ApproveEMRRequest, approved_by: str
) -> ProcExtraMaterialRequest:
    emr = await db.get(ProcExtraMaterialRequest, data.requestId)
    if not emr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EMR not found")
    if emr.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"EMR is already {emr.status}",
        )
    emr.status = "approved"
    emr.approved_by = approved_by
    emr.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(emr)
    return emr


async def reject_request(
    db: AsyncSession, request_id: str, data: RejectEMRRequest, reviewed_by: str
) -> ProcExtraMaterialRequest:
    try:
        rid = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid request ID"
        )

    emr = await db.get(ProcExtraMaterialRequest, rid)
    if not emr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EMR not found")
    if emr.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"EMR is already {emr.status}",
        )
    emr.status = "rejected"
    emr.rejection_reason = data.rejectionReason
    emr.approved_by = reviewed_by
    emr.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(emr)
    return emr
