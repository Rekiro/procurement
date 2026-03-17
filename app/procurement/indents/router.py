from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.procurement.indents import service
from app.procurement.indents.schemas import (
    IndentCreate, IndentCreateResponse, IndentUpdate,
    IndentListItem, IndentDetailResponse, IndentDetailProduct,
    ApproveIndentRequest, RejectIndentRequest,
)

router = APIRouter()


@router.post("", response_model=ApiResponse, status_code=201)
async def create_indent(
    data: IndentCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    indent = await service.create_indent(db, data)
    return success_response(IndentCreateResponse(
        message="Indent submitted successfully.",
        trackingNo=indent.tracking_no,
        status=indent.status,
    ).model_dump())


@router.get("", response_model=ApiResponse)
async def list_indents(
    status: str = Query(..., description="Filter by status, e.g. PENDING_PH_APPROVAL"),
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    rows, pagination = await service.list_indents(
        db, status_filter=status, search=search, page=page, limit=limit,
    )
    return success_response({
        "pagination": pagination,
        "indents": [
            IndentListItem(
                trackingNo=indent.tracking_no,
                monthYear=indent.for_month,
                requestDate=indent.created_at.strftime("%Y-%m-%d"),
                siteName=site_name or indent.site_id,
                branchName=None,
                category=indent.category,
                requestCategory=indent.request_category,
                siteBudget=None,
                value=float(indent.total_value),
                balance=None,
                status=indent.status,
            ).model_dump()
            for indent, site_name in rows
        ],
    })


@router.get("/my-indents", response_model=ApiResponse)
async def list_my_indents(
    requestor_email: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    indents = await service.list_my_indents(db, requestor_email)
    return success_response([{
        "trackingNo": i.tracking_no,
        "siteId": i.site_id,
        "forMonth": i.for_month,
        "category": i.category,
        "status": i.status,
        "totalValue": float(i.total_value),
        "createdAt": i.created_at.isoformat(),
    } for i in indents])


@router.post("/approve", response_model=ApiResponse)
async def approve_indent(
    data: ApproveIndentRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    results = await service.approve_indent(db, data, approved_by=user.sub)
    return success_response(results)



@router.get("/{tracking_no:path}", response_model=ApiResponse)
async def get_indent(
    tracking_no: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    indent, items, site_name = await service.get_indent_detail(db, tracking_no)
    products = await service.get_indent_detail_products(db, items)

    total_qty = sum(p["quantity"] for p in products)
    total_before_tax = sum(float(i.unit_price) * float(i.quantity) for i in items)
    total_after_tax = sum(p["amount"] for p in products)

    return success_response(IndentDetailResponse(
        trackingNo=indent.tracking_no,
        requestDate=indent.created_at.strftime("%Y-%m-%d"),
        monthYear=indent.for_month,
        branch=None,
        branchGst=indent.branch_gst,
        client=None,
        siteName=site_name,
        requestCategory=indent.request_category,
        categoryType=indent.category,
        narration=indent.narration,
        documentUrl=None,
        vendor="Multiple",
        products=[IndentDetailProduct(**p) for p in products],
        totalQty=total_qty,
        salesTotalBeforeTax=round(total_before_tax, 2),
        salesTotalAfterTax=round(total_after_tax, 2),
        purchaseTotalBeforeTax=round(total_before_tax, 2),
        purchaseTotalAfterTax=round(total_after_tax, 2),
    ).model_dump())


@router.post("/reject", response_model=ApiResponse)
async def reject_indent(
    data: RejectIndentRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    indent = await service.reject_indent(db, data.trackingNo, data, rejected_by=user.sub)
    return success_response({
        "trackingNo": indent.tracking_no,
        "status": indent.status,
    })


@router.put("/{tracking_no:path}", response_model=ApiResponse)
async def update_indent(
    tracking_no: str,
    data: IndentUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    await service.update_indent(db, tracking_no, data)
    indent, items, site_name = await service.get_indent_detail(db, tracking_no)
    products = await service.get_indent_detail_products(db, items)

    total_qty = sum(p["quantity"] for p in products)
    total_before_tax = sum(float(i.unit_price) * float(i.quantity) for i in items)
    total_after_tax = sum(p["amount"] for p in products)

    return success_response(IndentDetailResponse(
        trackingNo=indent.tracking_no,
        requestDate=indent.created_at.strftime("%Y-%m-%d"),
        monthYear=indent.for_month,
        branch=None,
        branchGst=indent.branch_gst,
        client=None,
        siteName=site_name,
        requestCategory=indent.request_category,
        categoryType=indent.category,
        narration=indent.narration,
        documentUrl=None,
        vendor="Multiple",
        products=[IndentDetailProduct(**p) for p in products],
        totalQty=total_qty,
        salesTotalBeforeTax=round(total_before_tax, 2),
        salesTotalAfterTax=round(total_after_tax, 2),
        purchaseTotalBeforeTax=round(total_before_tax, 2),
        purchaseTotalAfterTax=round(total_after_tax, 2),
    ).model_dump())


