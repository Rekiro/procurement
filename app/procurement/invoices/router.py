import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.shared.file_storage import upload_fastapi_file
from app.procurement.invoices import service
from app.procurement.invoices.schemas import (
    InvoiceSubmitData, InvoiceResponse,
    ApproveInvoiceRequest, RejectInvoiceRequest,
)

router = APIRouter()


@router.post("", response_model=ApiResponse, status_code=201)
async def submit_invoice(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    form = await request.form()

    data_str = form.get("data")
    if not data_str:
        raise HTTPException(status_code=400, detail="'data' field is required")
    try:
        data_dict = json.loads(data_str)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="'data' must be valid JSON")
    data = InvoiceSubmitData(**data_dict)

    bill_upload = form.get("billUpload")
    if not bill_upload or not hasattr(bill_upload, "read"):
        raise HTTPException(status_code=400, detail="'billUpload' file is required")
    _ext = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}
    ext = _ext.get(bill_upload.content_type, "bin")
    first_po = data.poNumbers[0] if data.poNumbers else "unknown"
    bill_url = await upload_fastapi_file(
        bill_upload, object_name=f"invoices/{first_po}/bill.{ext}"
    )

    invoice, po_numbers = await service.submit_invoice(db, data, bill_url=bill_url)
    return success_response(InvoiceResponse.from_orm(invoice, po_numbers=po_numbers).model_dump())


@router.get("", response_model=ApiResponse)
async def list_invoices(
    status: str | None = Query(None),
    search: str | None = Query(None),
    site: str | None = Query(None),
    state: str | None = Query(None),
    vendorCode: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    inv_list, pagination, filter_opts = await service.list_invoices_paginated(
        db,
        status_filter=status,
        search=search,
        site=site,
        state=state,
        vendor_code=vendorCode,
        page=page,
        limit=limit,
    )
    return success_response({
        "pagination": pagination,
        "filterOptions": filter_opts,
        "invoices": inv_list,
    })


@router.post("/approve", response_model=ApiResponse)
async def approve_invoices(
    data: ApproveInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    invoices = await service.approve_invoices(db, data.invoiceIds, reviewed_by=user.sub)
    results = []
    for inv in invoices:
        po_numbers = await service.get_invoice_po_numbers(db, inv.id)
        results.append(InvoiceResponse.from_orm(inv, po_numbers=po_numbers).model_dump())
    return success_response(results)


@router.post("/{invoice_id}/reject", response_model=ApiResponse)
async def reject_invoice(
    invoice_id: str,
    data: RejectInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    invoice = await service.reject_invoice(db, invoice_id, data, reviewed_by=user.sub)
    po_numbers = await service.get_invoice_po_numbers(db, invoice.id)
    return success_response(InvoiceResponse.from_orm(invoice, po_numbers=po_numbers).model_dump())
