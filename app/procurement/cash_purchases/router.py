import json

from fastapi import APIRouter, Depends, Query, Request, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.shared.file_storage import upload_fastapi_file
from app.procurement.cash_purchases import service
from app.procurement.cash_purchases.schemas import (
    CashPurchaseCreate, CashPurchaseListItem,
    ApproveCashPurchaseRequest, RejectCashPurchaseRequest,
)
from app.procurement.sites.service import get_site

router = APIRouter()


@router.post("", response_model=ApiResponse, status_code=201)
async def create_cash_purchase(
    request: Request,
    billUpload: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    form = await request.form()
    data_str = form.get("data")
    if not data_str:
        raise HTTPException(status_code=422, detail="'data' field is required")
    try:
        data = CashPurchaseCreate.model_validate(json.loads(data_str))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid data: {e}")

    purchase_id = await service.next_purchase_id(db)
    ext_map = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}
    ext = ext_map.get(billUpload.content_type, "pdf")
    bill_url = await upload_fastapi_file(
        billUpload, object_name=f"cash-purchases/{purchase_id}/bill.{ext}"
    )

    purchase = await service.create_cash_purchase(db, data, bill_url, purchase_id)

    site = await get_site(db, purchase.site_id)
    site_name = site.location_name if site else purchase.site_id
    return success_response({
        "purchaseId": purchase.purchase_id,
        "requesterName": purchase.requestor_email,
        "requestDate": purchase.created_at.strftime("%Y-%m-%d"),
        "forTheMonth": purchase.for_the_month.strftime("%B %Y"),
        "site": site_name,
        "vendorName": purchase.vendor_name,
        "gstNo": purchase.gst_no,
        "billUrl": purchase.bill_url,
        "products": purchase.products if isinstance(purchase.products, list) else [],
        "totalValue": float(purchase.total_cost),
        "status": purchase.status,
    })


@router.get("", response_model=ApiResponse)
async def list_cash_purchases(
    status: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    rows, pagination = await service.list_cash_purchases(
        db, status_filter=status, search=search, page=page, limit=limit,
    )
    return success_response({
        "pagination": pagination,
        "purchases": [
            CashPurchaseListItem(
                purchaseId=cp.purchase_id,
                requesterName=cp.requestor_email,
                requestDate=cp.created_at.strftime("%Y-%m-%d"),
                forTheMonth=cp.for_the_month.strftime("%B %Y") if cp.for_the_month else "",
                site=site_name or cp.site_id,
                vendorName=cp.vendor_name,
                gstNo=cp.gst_no,
                billUrl=cp.bill_url,
                products=[
                    {**p, "stock": p.get("quantity", p.get("stock", 0))}
                    for p in (cp.products if isinstance(cp.products, list) else [])
                ],
                totalValue=float(cp.total_cost),
                status=cp.status,
            ).model_dump()
            for cp, site_name in rows
        ],
    })


@router.post("/approve", response_model=ApiResponse)
async def approve_cash_purchases(
    data: ApproveCashPurchaseRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    results = await service.approve_cash_purchases(db, data, reviewed_by=user.sub)
    return success_response(results)


@router.post("/{purchase_id}/reject", response_model=ApiResponse)
async def reject_cash_purchase(
    purchase_id: str,
    data: RejectCashPurchaseRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    purchase = await service.reject_cash_purchase(db, purchase_id, data, reviewed_by=user.sub)
    return success_response({
        "purchaseId": purchase.purchase_id,
        "status": purchase.status,
        "reason": purchase.rejection_reason,
    })
