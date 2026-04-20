import math
from datetime import datetime
from app.shared.timezone import IST

from fastapi import HTTPException, status
from sqlalchemy import select, func, cast, String, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.cash_purchases.models import ProcCashPurchase
from app.procurement.cash_purchases.schemas import (
    CashPurchaseCreate, ApproveCashPurchaseRequest, RejectCashPurchaseRequest,
)
from app.procurement.sites.models import Site


def _parse_for_the_month(s: str) -> datetime:
    """Accept ISO date string or 'YYYY-MM'."""
    s = s.strip().rstrip("Z")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=IST)
        except ValueError:
            continue
    try:
        dt = datetime.strptime(s + "-01", "%Y-%m-%d")
        return dt.replace(tzinfo=IST)
    except ValueError:
        pass
    raise HTTPException(
        status_code=422,
        detail=f"Cannot parse forTheMonth '{s}'. Use ISO date like '2025-11-01T00:00:00.000Z'.",
    )


async def next_purchase_id(db: AsyncSession) -> str:
    count = await db.scalar(select(func.count()).select_from(ProcCashPurchase)) or 0
    return f"CP{count + 1:07d}"


async def create_cash_purchase(db: AsyncSession, data: CashPurchaseCreate, bill_url: str, purchase_id: str) -> ProcCashPurchase:
    for_the_month = _parse_for_the_month(data.forTheMonth)
    total_cost = sum(float(p.cost) for p in data.products)
    products_data = [p.model_dump() for p in data.products]

    purchase = ProcCashPurchase(
        purchase_id=purchase_id,
        requestor_email=data.requestorEmail,
        site_id=data.siteId,
        for_the_month=for_the_month,
        vendor_name=data.vendorName,
        gst_no=data.gstNo,
        products=products_data,
        total_cost=total_cost,
        bill_url=bill_url,
    )
    db.add(purchase)
    await db.commit()
    await db.refresh(purchase)
    return purchase


async def list_cash_purchases(
    db: AsyncSession,
    status_filter: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list, dict]:
    """Returns (list of (ProcCashPurchase, site_name) tuples, pagination dict)."""
    q = (
        select(ProcCashPurchase, Site.location_name)
        .outerjoin(Site, ProcCashPurchase.site_id == cast(Site.id, String))
        .order_by(ProcCashPurchase.created_at.desc())
    )
    if status_filter:
        q = q.where(ProcCashPurchase.status == status_filter)
    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                ProcCashPurchase.purchase_id.ilike(term),
                ProcCashPurchase.requestor_email.ilike(term),
                ProcCashPurchase.vendor_name.ilike(term),
            )
        )

    count_q = select(func.count()).select_from(q.subquery())
    total = await db.scalar(count_q) or 0

    offset = (page - 1) * limit
    result = await db.execute(q.offset(offset).limit(limit))
    rows = list(result.all())

    pagination = {
        "currentPage": page,
        "totalPages": math.ceil(total / limit) if limit else 1,
        "totalItems": total,
    }
    return rows, pagination


async def approve_cash_purchases(
    db: AsyncSession,
    data: ApproveCashPurchaseRequest,
    reviewed_by: str,
) -> list[dict]:
    result = await db.execute(
        select(ProcCashPurchase).where(ProcCashPurchase.purchase_id.in_(data.purchaseIds))
    )
    purchases = list(result.scalars().all())

    not_found = set(data.purchaseIds) - {p.purchase_id for p in purchases}
    if not_found:
        raise HTTPException(
            status_code=404,
            detail=f"Cash purchases not found: {', '.join(sorted(not_found))}",
        )

    not_pending = [p.purchase_id for p in purchases if p.status != "Pending"]
    if not_pending:
        raise HTTPException(
            status_code=409,
            detail=f"Cash purchases not in Pending status: {', '.join(sorted(not_pending))}",
        )

    now = datetime.now(IST)
    for purchase in purchases:
        purchase.status = "Approved"
        purchase.updated_at = now

    await db.commit()
    return [{"purchaseId": p.purchase_id, "status": p.status} for p in purchases]


async def reject_cash_purchase(
    db: AsyncSession,
    purchase_id: str,
    data: RejectCashPurchaseRequest,
    reviewed_by: str,
) -> ProcCashPurchase:
    purchase = await db.get(ProcCashPurchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Cash purchase not found")
    if purchase.status != "Pending":
        raise HTTPException(status_code=409, detail=f"Cash purchase is not in Pending status")

    purchase.status = "Rejected"
    purchase.rejection_reason = data.reason
    purchase.updated_at = datetime.now(IST)
    await db.commit()
    await db.refresh(purchase)
    return purchase
