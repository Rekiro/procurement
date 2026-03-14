import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.cash_purchases.models import ProcCashPurchase
from app.procurement.cash_purchases.schemas import (
    CashPurchaseCreate, ApproveCashPurchaseRequest, RejectCashPurchaseRequest,
)


async def create_cash_purchase(db: AsyncSession, data: CashPurchaseCreate, user_email: str):
    # Parse "YYYY-MM" → first day of that month
    year, month = map(int, data.forTheMonth.split("-"))
    for_the_month = datetime(year, month, 1, tzinfo=timezone.utc)

    count = await db.scalar(select(func.count()).select_from(ProcCashPurchase))
    purchase_id = f"CP-{(count or 0) + 1:06d}"

    products_data = [p.model_dump() for p in data.products]

    purchase = ProcCashPurchase(
        purchase_id=purchase_id,
        requestor_email=user_email,
        site_id=data.siteId,
        for_the_month=for_the_month,
        vendor_name=data.vendorName,
        gst_no=data.gstNo,
        products=products_data,
        total_cost=data.totalCost,
        bill_url=data.billUrl,
    )
    db.add(purchase)
    await db.commit()
    return purchase


async def list_cash_purchases(db: AsyncSession, status_filter: str | None = None):
    q = select(ProcCashPurchase).order_by(ProcCashPurchase.created_at.desc())
    if status_filter:
        q = q.where(ProcCashPurchase.status == status_filter)
    result = await db.execute(q)
    return list(result.scalars().all())


async def approve_cash_purchase(db: AsyncSession, data: ApproveCashPurchaseRequest,
                                reviewed_by: str):
    purchase = await db.get(ProcCashPurchase, data.purchaseId)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash purchase not found")
    if purchase.status != "Pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cash purchase is not in Pending status")

    purchase.status = "Approved"
    purchase.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(purchase)
    return purchase


async def reject_cash_purchase(db: AsyncSession, purchase_id: uuid.UUID,
                                data: RejectCashPurchaseRequest, reviewed_by: str):
    purchase = await db.get(ProcCashPurchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash purchase not found")
    if purchase.status != "Pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cash purchase is not in Pending status")

    purchase.status = "Rejected"
    purchase.rejection_reason = data.rejectionReason
    purchase.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(purchase)
    return purchase
