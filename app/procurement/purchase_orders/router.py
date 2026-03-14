from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.procurement.purchase_orders import service
from app.procurement.purchase_orders.schemas import (
    PoCreate, PoResponse, PoUpdateRequest,
    GrnCreate, GrnResponse,
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
    vendor_name = await service.get_vendor_name(db, po_obj.vendor_id)
    return success_response(PoResponse.from_orm(po_obj, items=items, vendor_name=vendor_name).model_dump())


@router.get("", response_model=ApiResponse)
async def list_purchase_orders(
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po_list, pagination = await service.list_purchase_orders_paginated(
        db, search=search, page=page, limit=limit,
    )
    return success_response({
        "pagination": pagination,
        "purchaseOrders": po_list,
    })


@router.get("/export")
async def export_purchase_orders(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    return await service.export_purchase_orders(db)


@router.get("/{po_number}/download")
async def download_po(
    po_number: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    raise NotImplementedError


@router.put("/{po_number}", response_model=ApiResponse)
async def update_purchase_order(
    po_number: str,
    data: PoUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    po = await service.update_purchase_order(db, po_number, data)
    vendor_name = await service.get_vendor_name(db, po.vendor_id)
    return success_response(PoResponse.from_orm(po, vendor_name=vendor_name).model_dump())


@router.post("/{po_number}/grn", response_model=ApiResponse, status_code=201)
async def submit_grn(
    po_number: str,
    data: GrnCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    grn = await service.submit_grn(db, po_number, data, user.sub)
    items, photos = await service.get_grn_with_details(db, grn.id)
    return success_response(GrnResponse.from_orm(grn, items=items, photos=photos).model_dump())
