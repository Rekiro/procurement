import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.procurement.uniform_requests import service
from app.procurement.uniform_requests.schemas import (
    UniformRequestCreate, UniformRequestResponse,
    UniformFulfillRequest, UniformRejectRequest,
    UniformPoUpdateRequest, UniformPoResponse,
    UniformGrnCreate, UniformConsolidatedItemsRequest,
    UniformInvoiceCreate, ApproveInvoiceRequest, RejectInvoiceRequest,
)
from app.procurement.invoices.schemas import InvoiceResponse
from app.procurement.invoices.service import get_invoice_po_numbers

router = APIRouter()


# --- Employee Search & Configuration ---

@router.get("/employees/uniform-search", response_model=ApiResponse)
async def search_employees(
    q: str = Query(default=""),
    user: TokenPayload = Depends(get_current_user),
):
    employees = await service.search_employees(q)
    return success_response(employees)


@router.get("/uniforms/configuration", response_model=ApiResponse)
async def get_uniform_configuration(
    user: TokenPayload = Depends(get_current_user),
):
    return success_response(service.get_uniform_configuration())


# --- Uniform Requests ---

@router.post("/uniform-requests", response_model=ApiResponse, status_code=201)
async def create_uniform_request(
    data: UniformRequestCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    req = await service.create_uniform_request(db, data, user.sub)
    return success_response(UniformRequestResponse.from_orm(req).model_dump())


@router.get("/uniform-requests", response_model=ApiResponse)
async def list_uniform_requests(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    reqs = await service.list_uniform_requests(db, status_filter=status)
    return success_response([UniformRequestResponse.from_orm(r).model_dump() for r in reqs])


@router.get("/employees/{employee_code}/uniform-history", response_model=ApiResponse)
async def get_employee_uniform_history(
    employee_code: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    reqs = await service.get_employee_uniform_history(db, employee_code)
    return success_response([UniformRequestResponse.from_orm(r).model_dump() for r in reqs])


@router.post("/uniform-requests/{request_id}/fulfill", response_model=ApiResponse, status_code=201)
async def fulfill_uniform_request(
    request_id: uuid.UUID,
    data: UniformFulfillRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po = await service.fulfill_uniform_request(db, request_id, data)
    vendor_name = await service.get_vendor_name(db, po.vendor_id)
    return success_response(UniformPoResponse.from_orm(po, vendor_name=vendor_name).model_dump())


@router.post("/uniform-requests/{request_id}/reject", response_model=ApiResponse)
async def reject_uniform_request(
    request_id: uuid.UUID,
    data: UniformRejectRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    req = await service.reject_uniform_request(db, request_id, data)
    return success_response(UniformRequestResponse.from_orm(req).model_dump())


# --- Uniform Purchase Orders ---

@router.get("/purchase-orders/uniform", response_model=ApiResponse)
async def list_uniform_pos(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    pos = await service.list_uniform_pos(db)
    result = []
    for po in pos:
        vendor_name = await service.get_vendor_name(db, po.vendor_id)
        result.append(UniformPoResponse.from_orm(po, vendor_name=vendor_name).model_dump())
    return success_response(result)


@router.get("/purchase-orders/uniform/export-all")
async def export_all_uniform_pos(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    pos = await service.list_uniform_pos(db)
    return await service.export_uniform_pos_excel(db, pos)


@router.get("/purchase-orders/uniform/{po_number}", response_model=ApiResponse)
async def get_uniform_po(
    po_number: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po = await service.get_uniform_po(db, po_number)
    vendor_name = await service.get_vendor_name(db, po.vendor_id)
    return success_response(UniformPoResponse.from_orm(po, vendor_name=vendor_name).model_dump())


@router.put("/purchase-orders/uniform/{po_number}", response_model=ApiResponse)
async def update_uniform_po(
    po_number: str,
    data: UniformPoUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po = await service.update_uniform_po(db, po_number, data)
    vendor_name = await service.get_vendor_name(db, po.vendor_id)
    return success_response(UniformPoResponse.from_orm(po, vendor_name=vendor_name).model_dump())


@router.get("/purchase-orders/uniform/{po_number}/pdf")
async def download_uniform_po_pdf(
    po_number: str,
    user: TokenPayload = Depends(get_current_user),
):
    raise HTTPException(status_code=501, detail="PDF generation not yet implemented")


@router.get("/purchase-orders/uniform/{po_number}/dc-pdf")
async def download_uniform_dc_pdf(
    po_number: str,
    user: TokenPayload = Depends(get_current_user),
):
    raise HTTPException(status_code=501, detail="PDF generation not yet implemented")


@router.get("/purchase-orders/uniform/{po_number}/export")
async def export_uniform_po(
    po_number: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po = await service.get_uniform_po(db, po_number)
    return await service.export_uniform_pos_excel(db, [po])


# --- Requestor Uniform Orders ---

@router.get("/requestor/uniform-orders", response_model=ApiResponse)
async def list_requestor_uniform_orders(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    pos = await service.list_uniform_pos(db)
    result = []
    for po in pos:
        vendor_name = await service.get_vendor_name(db, po.vendor_id)
        result.append(UniformPoResponse.from_orm(po, vendor_name=vendor_name).model_dump())
    return success_response(result)


@router.get("/requestor/uniform-orders/export")
async def export_requestor_uniform_orders(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    pos = await service.list_uniform_pos(db)
    return await service.export_uniform_pos_excel(db, pos)


@router.post("/purchase-orders/uniform/{po_number}/grn", response_model=ApiResponse, status_code=201)
async def submit_uniform_grn(
    po_number: str,
    data: UniformGrnCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po = await service.submit_uniform_grn(db, po_number, data, user.sub)
    vendor_name = await service.get_vendor_name(db, po.vendor_id)
    return success_response(UniformPoResponse.from_orm(po, vendor_name=vendor_name).model_dump())


# --- Consolidated Items ---

@router.post("/purchase-orders/uniform/consolidated-items", response_model=ApiResponse)
async def get_consolidated_uniform_items(
    data: UniformConsolidatedItemsRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    items = await service.get_consolidated_items(db, data.poNumbers)
    return success_response(items)


# --- Uniform Invoices ---

@router.post("/invoices/consolidated", response_model=ApiResponse, status_code=201)
async def submit_uniform_invoice(
    data: UniformInvoiceCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    invoice, po_numbers = await service.submit_uniform_invoice(db, data, user.sub)
    po_numbers_result = await get_invoice_po_numbers(db, invoice.id)
    return success_response(InvoiceResponse.from_orm(invoice, po_numbers=po_numbers_result).model_dump())
