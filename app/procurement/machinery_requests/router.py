import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.procurement.machinery_requests import service
from app.procurement.machinery_requests.schemas import (
    MachineryRequestCreate, MachineryRequestResponse,
    MachineryFulfillRequest, MachineryRejectRequest,
    MachineryPoUpdateRequest, MachineryPoResponse,
    MachineryGrnCreate, MachineryGrnResponse,
    MachineryConsolidatedItemsRequest,
    MachineryInvoiceCreate, ApproveInvoiceRequest, RejectInvoiceRequest,
)
from app.procurement.invoices.schemas import InvoiceResponse
from app.procurement.invoices.service import get_invoice_po_numbers

router = APIRouter()


# --- Machinery Options ---

@router.get("/machinery/options", response_model=ApiResponse)
async def get_machinery_options(
    user: TokenPayload = Depends(get_current_user),
):
    return success_response(service.get_machinery_options())


# --- Machinery Requests ---

@router.post("/machinery-requests", response_model=ApiResponse, status_code=201)
async def create_machinery_request(
    data: MachineryRequestCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    req = await service.create_machinery_request(db, data, user.sub)
    return success_response(MachineryRequestResponse.from_orm(req).model_dump())


@router.get("/machinery-requests", response_model=ApiResponse)
async def list_machinery_requests(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    reqs = await service.list_machinery_requests(db, status_filter=status)
    return success_response([MachineryRequestResponse.from_orm(r).model_dump() for r in reqs])


@router.get("/machinery-requests/{request_id}/details-for-approval", response_model=ApiResponse)
async def get_request_details_for_approval(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    req = await service.get_request_for_approval(db, request_id)
    return success_response(MachineryRequestResponse.from_orm(req).model_dump())


@router.post("/machinery-requests/{request_id}/fulfill", response_model=ApiResponse, status_code=201)
async def fulfill_machinery_request(
    request_id: uuid.UUID,
    data: MachineryFulfillRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po = await service.fulfill_machinery_request(db, request_id, data)
    vendor_name = await service.get_vendor_name(db, po.vendor_id)
    return success_response(MachineryPoResponse.from_orm(po, vendor_name=vendor_name).model_dump())


@router.post("/machinery-requests/{request_id}/reject", response_model=ApiResponse)
async def reject_machinery_request(
    request_id: uuid.UUID,
    data: MachineryRejectRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    req = await service.reject_machinery_request(db, request_id, data)
    return success_response(MachineryRequestResponse.from_orm(req).model_dump())


# --- Vendor Machinery POs ---

@router.get("/vendor/machinery-orders", response_model=ApiResponse)
async def list_vendor_machinery_orders(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    pos = await service.list_machinery_pos(db)
    result = []
    for po in pos:
        vendor_name = await service.get_vendor_name(db, po.vendor_id)
        result.append(MachineryPoResponse.from_orm(po, vendor_name=vendor_name).model_dump())
    return success_response(result)


@router.get("/vendor/machinery-orders/export-all")
async def export_all_machinery_orders(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    pos = await service.list_machinery_pos(db)
    return await service.export_machinery_pos_excel(db, pos)


@router.get("/purchase-orders/machinery/{po_number}", response_model=ApiResponse)
async def get_machinery_po(
    po_number: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po = await service.get_machinery_po(db, po_number)
    vendor_name = await service.get_vendor_name(db, po.vendor_id)
    return success_response(MachineryPoResponse.from_orm(po, vendor_name=vendor_name).model_dump())


@router.put("/purchase-orders/machinery/{po_number}", response_model=ApiResponse)
async def update_machinery_po(
    po_number: str,
    data: MachineryPoUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po = await service.update_machinery_po(db, po_number, data)
    vendor_name = await service.get_vendor_name(db, po.vendor_id)
    return success_response(MachineryPoResponse.from_orm(po, vendor_name=vendor_name).model_dump())


@router.get("/purchase-orders/machinery/{po_number}/pdf")
async def download_machinery_po_pdf(
    po_number: str,
    user: TokenPayload = Depends(get_current_user),
):
    raise HTTPException(status_code=501, detail="PDF generation not yet implemented")


@router.get("/purchase-orders/machinery/{po_number}/dc-pdf")
async def download_machinery_dc_pdf(
    po_number: str,
    user: TokenPayload = Depends(get_current_user),
):
    raise HTTPException(status_code=501, detail="PDF generation not yet implemented")


@router.get("/purchase-orders/machinery/{po_number}/export")
async def export_machinery_po(
    po_number: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po = await service.get_machinery_po(db, po_number)
    return await service.export_machinery_pos_excel(db, [po])


# --- Requestor Machinery Orders ---

@router.get("/requestor/machinery-orders", response_model=ApiResponse)
async def list_requestor_machinery_orders(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    pos = await service.list_machinery_pos(db)
    result = []
    for po in pos:
        vendor_name = await service.get_vendor_name(db, po.vendor_id)
        result.append(MachineryPoResponse.from_orm(po, vendor_name=vendor_name).model_dump())
    return success_response(result)


@router.get("/requestor/machinery-orders/export")
async def export_requestor_machinery_orders(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    pos = await service.list_machinery_pos(db)
    return await service.export_machinery_pos_excel(db, pos)


@router.post("/purchase-orders/machinery/{po_number}/grn", response_model=ApiResponse,
             status_code=201)
async def submit_machinery_grn(
    po_number: str,
    data: MachineryGrnCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    grn = await service.submit_machinery_grn(db, po_number, data, user.sub)
    return success_response(MachineryGrnResponse.from_orm(grn).model_dump())


# --- Consolidated Items (for invoicing multiple POs) ---

@router.post("/purchase-orders/machinery/consolidated-items", response_model=ApiResponse)
async def get_consolidated_machinery_items(
    data: MachineryConsolidatedItemsRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    items = await service.get_consolidated_items(db, data.poNumbers)
    return success_response(items)


# --- Machinery Invoices ---

@router.post("/invoices/consolidated/machinery", response_model=ApiResponse, status_code=201)
async def submit_machinery_invoice(
    data: MachineryInvoiceCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    invoice, po_numbers = await service.submit_machinery_invoice(db, data, user.sub)
    po_numbers_result = await get_invoice_po_numbers(db, invoice.id)
    return success_response(InvoiceResponse.from_orm(invoice, po_numbers=po_numbers_result).model_dump())


@router.get("/invoices/machinery/approval-list", response_model=ApiResponse)
async def list_machinery_invoice_approvals(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    invoices = await service.list_machinery_invoices(db)
    result = []
    for inv in invoices:
        po_numbers = await get_invoice_po_numbers(db, inv.id)
        result.append(InvoiceResponse.from_orm(inv, po_numbers=po_numbers).model_dump())
    return success_response(result)


@router.post("/invoices/machinery/approve", response_model=ApiResponse)
async def approve_machinery_invoice(
    data: ApproveInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    invoice = await service.approve_machinery_invoice(db, data, reviewed_by=user.sub)
    po_numbers = await get_invoice_po_numbers(db, invoice.id)
    return success_response(InvoiceResponse.from_orm(invoice, po_numbers=po_numbers).model_dump())


@router.post("/invoices/machinery/{invoice_id}/reject", response_model=ApiResponse)
async def reject_machinery_invoice(
    invoice_id: uuid.UUID,
    data: RejectInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    invoice = await service.reject_machinery_invoice(db, invoice_id, data, reviewed_by=user.sub)
    po_numbers = await get_invoice_po_numbers(db, invoice.id)
    return success_response(InvoiceResponse.from_orm(invoice, po_numbers=po_numbers).model_dump())


# --- GRN Evidence ---

@router.get("/machinery/grn/{po_number}/evidence", response_model=ApiResponse)
async def get_machinery_grn_evidence(
    po_number: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    grn = await service.get_machinery_grn_evidence(db, po_number)
    return success_response(MachineryGrnResponse.from_orm(grn).model_dump())
