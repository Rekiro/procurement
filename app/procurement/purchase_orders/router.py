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
    PoResponse, PoUpdateData,
    GrnData, GrnResponse,
)

router = APIRouter()


@router.get("", response_model=ApiResponse)
async def list_purchase_orders(
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    vendorCode: str | None = None,
    requestorEmail: str | None = None,
    status: str | None = None,
    state: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po_list, pagination, available_states = await service.list_purchase_orders_paginated(
        db, search=search, page=page, limit=limit,
        vendor_code=vendorCode, requestor_email=requestorEmail,
        status=status, state=state,
    )
    return success_response({
        "pagination": pagination,
        "availableStates": available_states,
        "purchaseOrders": po_list,
    })


@router.get("/export")
async def export_purchase_orders(
    search: str | None = None,
    vendorCode: str | None = None,
    requestorEmail: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    return await service.export_purchase_orders(
        db, search=search, vendor_code=vendorCode, requestor_email=requestorEmail
    )


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

    _ext = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}

    # Upload files if provided (human-readable object names)
    pod_image_url = None
    signed_pod_url = None
    signed_dc_url = None

    pod_image = form.get("podImage")
    if pod_image and hasattr(pod_image, "read"):
        ext = _ext.get(pod_image.content_type, "bin")
        pod_image_url = await upload_fastapi_file(
            pod_image, object_name=f"purchase-orders/{po_number}/pod_image.{ext}"
        )

    signed_pod = form.get("signedPod")
    if signed_pod and hasattr(signed_pod, "read"):
        ext = _ext.get(signed_pod.content_type, "bin")
        signed_pod_url = await upload_fastapi_file(
            signed_pod, object_name=f"purchase-orders/{po_number}/signed_pod.{ext}"
        )

    signed_dc = form.get("signedDc")
    if signed_dc and hasattr(signed_dc, "read"):
        ext = _ext.get(signed_dc.content_type, "bin")
        signed_dc_url = await upload_fastapi_file(
            signed_dc, object_name=f"purchase-orders/{po_number}/signed_dc.{ext}"
        )

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

    _ext = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}

    # signedDc file is required
    signed_dc = form.get("signedDc")
    if not signed_dc or not hasattr(signed_dc, "read"):
        raise HTTPException(status_code=400, detail="'signedDc' file is required")
    ext = _ext.get(signed_dc.content_type, "bin")
    signed_dc_url = await upload_fastapi_file(
        signed_dc, object_name=f"grn/{po_number}/signed_dc.{ext}"
    )

    # Optional photos (up to 2)
    photo_urls = []
    photo_files = form.getlist("photos")
    for photo_file in photo_files:
        if hasattr(photo_file, "read"):
            if len(photo_urls) >= 2:
                raise HTTPException(status_code=400, detail="Maximum 2 photos allowed")
            ext = _ext.get(photo_file.content_type, "bin")
            url = await upload_fastapi_file(
                photo_file, object_name=f"grn/{po_number}/photo_{len(photo_urls) + 1}.{ext}"
            )
            photo_urls.append(url)

    grn = await service.submit_grn(
        db, po_number, data,
        signed_dc_url=signed_dc_url,
        photo_urls=photo_urls,
    )
    items, photos = await service.get_grn_with_details(db, grn.id)
    return success_response(GrnResponse.from_orm(grn, items=items, photos=photos).model_dump())
