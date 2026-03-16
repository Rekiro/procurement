import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.shared.file_storage import upload_fastapi_file
from app.procurement.purchase_orders import service
from app.procurement.purchase_orders.schemas import (
    PoCreate, PoResponse, PoUpdateData,
    GrnData, GrnResponse,
)

router = APIRouter()


@router.post("", response_model=ApiResponse, status_code=201)
async def create_purchase_order(
    data: PoCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po = await service.create_purchase_order(db, data, user.sub)
    po_obj, items = await service.get_po_with_items(db, po.po_number)
    vendor_name = await service.get_vendor_name(db, po_obj.vendor_code)
    return success_response(PoResponse.from_orm(po_obj, items=items, vendor_name=vendor_name).model_dump())


@router.get("", response_model=ApiResponse)
async def list_purchase_orders(
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    vendorCode: str | None = None,
    requestorEmail: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po_list, pagination = await service.list_purchase_orders_paginated(
        db, search=search, page=page, limit=limit,
        vendor_code=vendorCode, requestor_email=requestorEmail,
    )
    return success_response({
        "pagination": pagination,
        "purchaseOrders": po_list,
    })


@router.get("/export")
async def export_purchase_orders(
    search: str | None = None,
    vendorCode: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    return await service.export_purchase_orders(db, search=search, vendor_code=vendorCode)


@router.get("/{po_number}/download")
async def download_po(
    po_number: str,
    type: str = Query(..., description="Document type: po_pdf, po_excel, dc_pdf"),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    if type not in ("po_pdf", "po_excel", "dc_pdf"):
        raise HTTPException(status_code=400, detail="Invalid type. Must be: po_pdf, po_excel, dc_pdf")

    if type == "po_excel":
        return await service.download_po_excel(db, po_number)

    # PDF types not yet implemented
    await service.get_po_with_items(db, po_number)  # verify PO exists
    raise HTTPException(
        status_code=501,
        detail=f"Document download ({type}) not yet implemented. Requires PDF generation library.",
    )


@router.put("/{po_number}", response_model=ApiResponse)
async def update_purchase_order(
    po_number: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    form = await request.form()

    # Parse 'data' JSON string
    data_str = form.get("data")
    if not data_str:
        raise HTTPException(status_code=400, detail="'data' field is required")
    try:
        data_dict = json.loads(data_str)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="'data' must be valid JSON")
    data = PoUpdateData(**data_dict)

    # Upload files if provided
    pod_image_url = None
    signed_pod_url = None
    signed_dc_url = None

    pod_image = form.get("podImage")
    if pod_image and hasattr(pod_image, "read"):
        pod_image_url = await upload_fastapi_file(pod_image, prefix=f"purchase-orders/{po_number}")

    signed_pod = form.get("signedPod")
    if signed_pod and hasattr(signed_pod, "read"):
        signed_pod_url = await upload_fastapi_file(signed_pod, prefix=f"purchase-orders/{po_number}")

    signed_dc = form.get("signedDc")
    if signed_dc and hasattr(signed_dc, "read"):
        signed_dc_url = await upload_fastapi_file(signed_dc, prefix=f"purchase-orders/{po_number}")

    po = await service.update_purchase_order(
        db, po_number, data,
        pod_image_url=pod_image_url,
        signed_pod_url=signed_pod_url,
        signed_dc_url=signed_dc_url,
    )
    vendor_name = await service.get_vendor_name(db, po.vendor_code)
    return success_response(PoResponse.from_orm(po, vendor_name=vendor_name).model_dump())


@router.post("/{po_number}/grn", response_model=ApiResponse, status_code=201)
async def submit_grn(
    po_number: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    form = await request.form()

    # Parse 'data' JSON string
    data_str = form.get("data")
    if not data_str:
        raise HTTPException(status_code=400, detail="'data' field is required")
    try:
        data_dict = json.loads(data_str)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="'data' must be valid JSON")
    data = GrnData(**data_dict)

    # signedDc file is required
    signed_dc = form.get("signedDc")
    if not signed_dc or not hasattr(signed_dc, "read"):
        raise HTTPException(status_code=400, detail="'signedDc' file is required")
    signed_dc_url = await upload_fastapi_file(signed_dc, prefix=f"grn/{po_number}")

    # Optional photos (up to 2)
    photo_urls = []
    photo_files = form.getlist("photos")
    for photo_file in photo_files:
        if hasattr(photo_file, "read"):
            if len(photo_urls) >= 2:
                raise HTTPException(status_code=400, detail="Maximum 2 photos allowed")
            url = await upload_fastapi_file(photo_file, prefix=f"grn/{po_number}/photos")
            photo_urls.append(url)

    grn = await service.submit_grn(
        db, po_number, data,
        signed_dc_url=signed_dc_url,
        photo_urls=photo_urls,
    )
    items, photos = await service.get_grn_with_details(db, grn.id)
    return success_response(GrnResponse.from_orm(grn, items=items, photos=photos).model_dump())
