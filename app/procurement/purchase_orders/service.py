import math
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.purchase_orders.models import (
    ProcPurchaseOrder, ProcPoItem, ProcGrn, ProcGrnItem, ProcGrnPhoto,
)
from app.procurement.purchase_orders.schemas import PoCreate, PoUpdateRequest, GrnCreate
from app.procurement.indents.models import ProcIndent
from app.procurement.vendors.models import ProcVendor
from app.procurement.sites.models import Site


async def create_purchase_order(db: AsyncSession, data: PoCreate, created_by: str):
    indent = await db.get(ProcIndent, data.indentId)
    if not indent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indent not found")
    if indent.status != "PH_APPROVED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Indent must be PH_APPROVED to create a PO")

    vendor = await db.get(ProcVendor, data.vendorId)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    if vendor.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Vendor must be ACTIVE to create a PO")

    now = datetime.now(timezone.utc)
    count = await db.scalar(select(func.count()).select_from(ProcPurchaseOrder))
    po_number = f"PO-{now.strftime('%Y%m')}-{(count or 0) + 1:04d}"

    expected_delivery = None
    tat = None
    if data.expectedDeliveryDate:
        expected_delivery = datetime(
            data.expectedDeliveryDate.year,
            data.expectedDeliveryDate.month,
            data.expectedDeliveryDate.day,
            tzinfo=timezone.utc,
        )
        tat = (data.expectedDeliveryDate - now.date()).days

    total_value = sum(item.quantity * item.landedPrice for item in data.items)

    po = ProcPurchaseOrder(
        po_number=po_number,
        indent_id=data.indentId,
        vendor_id=data.vendorId,
        site_id=indent.site_id,
        po_date=now,
        expected_delivery_date=expected_delivery,
        tat=tat,
        tat_status="On Time" if tat and tat >= 0 else None,
        status="Not Delivered",
        total_value=total_value,
    )
    db.add(po)
    await db.flush()

    for item in data.items:
        item_id = str(item.indentItemId) if item.indentItemId else str(uuid.uuid4())
        db.add(ProcPoItem(
            po_id=po.id,
            item_id=item_id,
            product_code=item.productId,
            product_name=item.productName,
            quantity=item.quantity,
            landed_price=item.landedPrice,
            total_amount=item.quantity * item.landedPrice,
        ))

    indent.status = "PO_CREATED"
    await db.commit()
    return po


async def get_po_with_items(db: AsyncSession, po_number: str):
    po = await db.scalar(
        select(ProcPurchaseOrder).where(ProcPurchaseOrder.po_number == po_number)
    )
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    result = await db.execute(select(ProcPoItem).where(ProcPoItem.po_id == po.id))
    items = list(result.scalars().all())
    return po, items


async def list_purchase_orders(db: AsyncSession):
    """Legacy: returns flat list (used by export)."""
    result = await db.execute(
        select(ProcPurchaseOrder).order_by(ProcPurchaseOrder.created_at.desc())
    )
    return list(result.scalars().all())


async def list_purchase_orders_paginated(
    db: AsyncSession,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[dict], dict]:
    """Paginated PO list with site name and indent tracking_no joins."""
    q = (
        select(
            ProcPurchaseOrder,
            ProcIndent.tracking_no.label("indent_tracking_no"),
            Site.location_name.label("site_name"),
        )
        .outerjoin(ProcIndent, ProcPurchaseOrder.indent_id == ProcIndent.id)
        .outerjoin(Site, ProcPurchaseOrder.site_id == cast(Site.id, String))
        .order_by(ProcPurchaseOrder.created_at.desc())
    )

    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                ProcPurchaseOrder.po_number.ilike(term),
                ProcPurchaseOrder.status.ilike(term),
                Site.location_name.ilike(term),
                ProcIndent.tracking_no.ilike(term),
            )
        )

    count_q = select(func.count()).select_from(q.subquery())
    total = await db.scalar(count_q) or 0

    offset = (page - 1) * limit
    result = await db.execute(q.offset(offset).limit(limit))
    rows = list(result.all())

    def _fmt_date(d) -> str | None:
        if d is None:
            return None
        if hasattr(d, "strftime"):
            return d.strftime("%Y-%m-%d")
        return str(d)

    po_list = []
    for po, indent_tracking_no, site_name in rows:
        po_list.append({
            "materialRequestId": indent_tracking_no,
            "siteName": site_name or po.site_id,
            "region": None,
            "poNumber": po.po_number,
            "poDate": _fmt_date(po.po_date),
            "deliveryType": po.delivery_type,
            "tat": po.tat,
            "expectedDeliveryDate": _fmt_date(po.expected_delivery_date),
            "status": po.status,
            "courierName": po.courier_name,
            "podNumber": po.pod_number,
            "dateOfDelivery": _fmt_date(po.date_of_delivery),
            "podImageUrl": po.pod_image_url,
            "signedPodUrl": po.signed_pod_url,
            "signedDcUrl": po.signed_dc_url,
            "tatStatus": po.tat_status,
            "reason": po.reason,
        })

    pagination = {
        "currentPage": page,
        "totalPages": math.ceil(total / limit) if limit else 1,
        "totalItems": total,
    }
    return po_list, pagination


async def update_purchase_order(db: AsyncSession, po_number: str, data: PoUpdateRequest):
    po = await db.scalar(
        select(ProcPurchaseOrder).where(ProcPurchaseOrder.po_number == po_number)
    )
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")

    if data.status is not None:
        po.status = data.status
        if data.status == "Delivered":
            po.date_of_delivery = datetime.now(timezone.utc)
    if data.deliveryType is not None:
        po.delivery_type = data.deliveryType
    if data.courierName is not None:
        po.courier_name = data.courierName
    if data.podNumber is not None:
        po.pod_number = data.podNumber

    po.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(po)
    return po


async def submit_grn(db: AsyncSession, po_number: str, data: GrnCreate, user_email: str):
    po = await db.scalar(
        select(ProcPurchaseOrder).where(ProcPurchaseOrder.po_number == po_number)
    )
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")

    existing = await db.scalar(select(ProcGrn).where(ProcGrn.po_id == po.id))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="GRN already submitted for this PO")

    grn = ProcGrn(
        po_id=po.id,
        po_number=po_number,
        requestor_email=user_email,
        predefined_comment=data.predefinedComment,
        comments=data.comments,
        signed_dc_url=data.signedDcUrl,
    )
    db.add(grn)
    await db.flush()

    for item in data.items:
        db.add(ProcGrnItem(
            grn_id=grn.id,
            item_id=item.itemId,
            item_name=item.itemName,
            ordered_quantity=item.orderedQuantity,
            received_quantity=item.receivedQuantity,
            is_accepted=item.isAccepted,
        ))

    for url in data.photoUrls:
        db.add(ProcGrnPhoto(grn_id=grn.id, photo_url=url))

    po.status = "Delivered"
    po.date_of_delivery = datetime.now(timezone.utc)
    po.signed_dc_url = data.signedDcUrl
    po.updated_at = datetime.now(timezone.utc)

    await db.commit()
    return grn


async def get_grn_with_details(db: AsyncSession, grn_id: uuid.UUID):
    result_items = await db.execute(select(ProcGrnItem).where(ProcGrnItem.grn_id == grn_id))
    items = list(result_items.scalars().all())
    result_photos = await db.execute(select(ProcGrnPhoto).where(ProcGrnPhoto.grn_id == grn_id))
    photos = list(result_photos.scalars().all())
    return items, photos


async def export_purchase_orders(db: AsyncSession):
    from openpyxl import Workbook
    from app.shared.excel_utils import workbook_to_streaming_response

    pos = await list_purchase_orders(db)

    wb = Workbook()
    ws = wb.active
    ws.title = "Purchase Orders"

    headers = [
        "PO Number", "Site ID", "Status", "Total Value (INR)",
        "PO Date", "Expected Delivery", "Delivery Type",
        "Courier", "POD Number", "Date of Delivery",
    ]
    ws.append(headers)

    from app.shared.excel_utils import HEADER_FONT, HEADER_FILL, HEADER_BORDER
    from openpyxl.styles import Alignment
    from openpyxl.utils import get_column_letter

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = HEADER_BORDER
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[get_column_letter(col_idx)].width = max(len(header) + 4, 18)

    for po in pos:
        ws.append([
            po.po_number,
            po.site_id,
            po.status,
            float(po.total_value),
            po.po_date.strftime("%Y-%m-%d") if po.po_date else "",
            po.expected_delivery_date.strftime("%Y-%m-%d") if po.expected_delivery_date else "",
            po.delivery_type or "",
            po.courier_name or "",
            po.pod_number or "",
            po.date_of_delivery.strftime("%Y-%m-%d") if po.date_of_delivery else "",
        ])

    ws.freeze_panes = "A2"
    return workbook_to_streaming_response(wb, "purchase_orders.xlsx")


async def get_vendor_name(db: AsyncSession, vendor_id: uuid.UUID | None) -> str | None:
    if not vendor_id:
        return None
    vendor = await db.get(ProcVendor, vendor_id)
    return vendor.company_name if vendor else None
