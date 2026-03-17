import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func, extract, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.extra_material_requests.models import ProcExtraMaterialRequest
from app.procurement.extra_material_requests.schemas import (
    ExtraMaterialRequestCreate,
    ApproveEMRRequest,
    RejectEMRRequest,
)
from app.procurement.sites.models import Site


def _parse_month_year(s: str) -> datetime:
    """Accept ISO date string ('2025-11-01T00:00:00.000Z') or 'YYYY-MM'."""
    s = s.strip().rstrip("Z")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        except ValueError:
            continue
    # Try YYYY-MM
    try:
        dt = datetime.strptime(s + "-01", "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    raise HTTPException(
        status_code=422,
        detail=f"Cannot parse monthYear '{s}'. Use ISO date like '2025-11-01T00:00:00.000Z'.",
    )


async def _next_emr_id(db: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    year_count = await db.scalar(
        select(func.count()).select_from(ProcExtraMaterialRequest).where(
            extract("year", ProcExtraMaterialRequest.created_at) == year
        )
    )
    return f"EMR-{year}-{(year_count or 0) + 1:03d}"


async def get_status(db: AsyncSession, requestor_email: str, site_id: str) -> dict:
    """Return {status: none|pending|approved, emrId?} for current month."""
    site = await db.scalar(select(Site).where(cast(Site.id, String) == site_id))
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found")

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ProcExtraMaterialRequest)
        .where(ProcExtraMaterialRequest.requestor_email == requestor_email)
        .where(ProcExtraMaterialRequest.site_id == site_id)
        .where(ProcExtraMaterialRequest.status.in_(["pending", "approved"]))
        .where(extract("year", ProcExtraMaterialRequest.month_year) == now.year)
        .where(extract("month", ProcExtraMaterialRequest.month_year) == now.month)
        .order_by(ProcExtraMaterialRequest.created_at.desc())
        .limit(1)
    )
    emr = result.scalars().first()
    if emr is None:
        return {"status": "none"}
    return {
        "status": emr.status,
        "emrId": emr.emr_id,
    }


async def create_request(
    db: AsyncSession, data: ExtraMaterialRequestCreate
) -> ProcExtraMaterialRequest:
    month_year_dt = _parse_month_year(data.monthYear)

    # Validate site exists
    site = await db.scalar(
        select(Site).where(cast(Site.id, String) == data.siteId)
    )
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{data.siteId}' not found")

    # One pending/approved EMR per requestor+site per month
    existing = await db.execute(
        select(ProcExtraMaterialRequest)
        .where(ProcExtraMaterialRequest.requestor_email == data.requestorEmail)
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

    emr_id = await _next_emr_id(db)
    emr = ProcExtraMaterialRequest(
        emr_id=emr_id,
        site_id=data.siteId,
        requestor_email=data.requestorEmail,
        month_year=month_year_dt,
        reason=data.reason,
        status="pending",
    )
    db.add(emr)
    await db.commit()
    await db.refresh(emr)
    return emr


async def list_requests_paginated(
    db: AsyncSession,
    status_filter: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[dict], dict]:
    q = (
        select(ProcExtraMaterialRequest, Site.location_name.label("site_name"))
        .outerjoin(Site, ProcExtraMaterialRequest.site_id == cast(Site.id, String))
        .order_by(ProcExtraMaterialRequest.created_at.desc())
    )
    if status_filter:
        q = q.where(ProcExtraMaterialRequest.status == status_filter)

    count_q = select(func.count()).select_from(q.subquery())
    total = await db.scalar(count_q) or 0

    offset = (page - 1) * limit
    result = await db.execute(q.offset(offset).limit(limit))
    rows = list(result.all())

    requests_list = []
    for emr, site_name in rows:
        requests_list.append({
            "emrId": emr.emr_id,
            "siteName": site_name or emr.site_id,
            "monthYear": emr.month_year.strftime("%B %Y") if emr.month_year else "",
            "reason": emr.reason,
            "requesterName": emr.requestor_email,
            "requestDate": emr.created_at.isoformat(),
            "status": emr.status,
        })

    pagination = {
        "currentPage": page,
        "totalPages": math.ceil(total / limit) if limit else 1,
        "totalItems": total,
    }
    return requests_list, pagination


async def approve_requests(
    db: AsyncSession, request_ids: list[str], approved_by: str
) -> list[ProcExtraMaterialRequest]:
    result = await db.execute(
        select(ProcExtraMaterialRequest).where(
            ProcExtraMaterialRequest.emr_id.in_(request_ids)
        )
    )
    emrs = list(result.scalars().all())

    not_found = set(request_ids) - {e.emr_id for e in emrs}
    if not_found:
        raise HTTPException(
            status_code=404,
            detail=f"EMRs not found: {', '.join(sorted(not_found))}",
        )

    not_pending = [e.emr_id for e in emrs if e.status != "pending"]
    if not_pending:
        raise HTTPException(
            status_code=409,
            detail=f"EMRs not in pending status: {', '.join(sorted(not_pending))}",
        )

    for emr in emrs:
        emr.status = "approved"
        emr.approved_by = approved_by
        emr.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    return emrs


async def reject_request(
    db: AsyncSession, emr_id: str, data: RejectEMRRequest, reviewed_by: str
) -> ProcExtraMaterialRequest:
    emr = await db.scalar(
        select(ProcExtraMaterialRequest).where(
            ProcExtraMaterialRequest.emr_id == emr_id
        )
    )
    if not emr:
        raise HTTPException(status_code=404, detail="EMR not found")
    if emr.status != "pending":
        raise HTTPException(
            status_code=409, detail=f"EMR is already {emr.status}"
        )
    emr.status = "rejected"
    emr.rejection_reason = data.reason
    emr.approved_by = reviewed_by
    emr.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(emr)
    return emr
