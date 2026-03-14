import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.procurement.invoices import service
from app.procurement.invoices.schemas import (
    InvoiceCreate, InvoiceResponse,
    ApproveInvoiceRequest, RejectInvoiceRequest,
)

router = APIRouter()


@router.post("", response_model=ApiResponse, status_code=201)
async def submit_invoice(
    data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    invoice, po_numbers = await service.submit_invoice(db, data, user.sub)
    return success_response(InvoiceResponse.from_orm(invoice, po_numbers=po_numbers).model_dump())


@router.get("", response_model=ApiResponse)
async def list_invoices(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    invoices = await service.list_invoices(db, status_filter=status)
    result = []
    for inv in invoices:
        po_numbers = await service.get_invoice_po_numbers(db, inv.id)
        result.append(InvoiceResponse.from_orm(inv, po_numbers=po_numbers).model_dump())
    return success_response(result)


@router.post("/approve", response_model=ApiResponse)
async def approve_invoice(
    data: ApproveInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    invoice = await service.approve_invoice(db, data, reviewed_by=user.sub)
    po_numbers = await service.get_invoice_po_numbers(db, invoice.id)
    return success_response(InvoiceResponse.from_orm(invoice, po_numbers=po_numbers).model_dump())


@router.post("/{invoice_id}/reject", response_model=ApiResponse)
async def reject_invoice(
    invoice_id: uuid.UUID,
    data: RejectInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    invoice = await service.reject_invoice(db, invoice_id, data, reviewed_by=user.sub)
    po_numbers = await service.get_invoice_po_numbers(db, invoice.id)
    return success_response(InvoiceResponse.from_orm(invoice, po_numbers=po_numbers).model_dump())
