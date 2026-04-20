import math
import uuid
from datetime import datetime
from app.shared.timezone import IST

from fastapi import HTTPException, status
from sqlalchemy import select, func, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.indents.models import ProcIndent, ProcIndentItem
from app.procurement.indents.schemas import IndentCreate, IndentUpdate, ApproveIndentRequest, RejectIndentRequest
from app.procurement.products.models import ProcProduct
from app.procurement.vendors.models import ProcVendor
from app.procurement.extra_material_requests.models import ProcExtraMaterialRequest
from app.procurement.sites.models import Site
from app.procurement.purchase_orders.models import ProcPurchaseOrder, ProcPoItem


async def _next_tracking_no(db: AsyncSession) -> str:
    year = datetime.now(IST).year
    count = await db.scalar(select(func.count()).select_from(ProcIndent)) or 0
    return f"IND/{year}/{count + 1:05d}"


async def create_indent(db: AsyncSession, data: IndentCreate) -> ProcIndent:
    # Look up all products and build price/name map
    product_codes = [item.productCode for item in data.items]
    result = await db.execute(
        select(ProcProduct, ProcVendor.company_name)
        .join(ProcVendor, ProcProduct.vendor_code == ProcVendor.vendor_code)
        .where(ProcProduct.product_code.in_(product_codes))
    )
    product_map = {}
    for prod, vendor_name in result.all():
        product_map[prod.product_code] = (prod, vendor_name)

    # Validate all products exist
    for code in product_codes:
        if code not in product_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {code} not found",
            )

    # Calculate total value
    total_value = 0.0
    for item in data.items:
        prod, _ = product_map[item.productCode]
        total_value += float(prod.final_price) * item.quantity

    # Category-based workflow
    if data.category == "Regular":
        # Budget check placeholder: exclude "Human Consumables" from budget total
        # Budget data not yet available in sites table — skip actual check for now
        initial_status = "PENDING_PH_APPROVAL"

    elif data.category == "Extra Material":
        # Validate EMR
        if not data.extraMaterialRequestId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="extraMaterialRequestId is required for Extra Material indents",
            )

        emr = await db.get(ProcExtraMaterialRequest, data.extraMaterialRequestId)
        if not emr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extra material request not found",
            )
        if emr.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extra material request is not approved (status: {emr.status})",
            )
        if emr.site_id != data.siteId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="EMR site does not match indent site",
            )

        # Close EMR (single-use permission)
        emr.status = "closed"

        initial_status = "PENDING_RM_APPROVAL"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category must be 'Regular' or 'Extra Material'",
        )

    tracking_no = await _next_tracking_no(db)

    indent = ProcIndent(
        tracking_no=tracking_no,
        requestor_email=data.requestorEmail,
        site_id=data.siteId,
        for_month=data.forMonth,
        is_monthly=data.isMonthly,
        category=data.category,
        emr_id=data.extraMaterialRequestId or None,
        total_value=total_value,
        status=initial_status,
    )
    db.add(indent)
    await db.flush()

    for item in data.items:
        prod, _ = product_map[item.productCode]
        unit_price = float(prod.final_price)
        db.add(ProcIndentItem(
            indent_id=indent.id,
            product_code=prod.product_code,
            product_name=prod.product_name,
            quantity=item.quantity,
            size=item.size,
            unit_price=unit_price,
            total_price=unit_price * item.quantity,
        ))

    await db.commit()
    await db.refresh(indent)
    return indent


async def list_indents(
    db: AsyncSession,
    status_filter: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list, dict]:
    """Returns (list of (ProcIndent, site_name) tuples, pagination dict)."""
    q = (
        select(ProcIndent, Site.location_name)
        .outerjoin(Site, ProcIndent.site_id == cast(Site.id, String))
        .order_by(ProcIndent.created_at.desc())
    )
    if status_filter:
        q = q.where(ProcIndent.status == status_filter)
    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                ProcIndent.tracking_no.ilike(term),
                ProcIndent.site_id.ilike(term),
            )
        )

    # Manual pagination (query returns tuples)
    count_q = select(func.count()).select_from(q.subquery())
    total = await db.scalar(count_q) or 0

    if page < 1:
        page = 1
    if limit < 1:
        limit = 10
    offset = (page - 1) * limit
    result = await db.execute(q.offset(offset).limit(limit))
    rows = list(result.all())

    pagination = {
        "currentPage": page,
        "totalPages": math.ceil(total / limit) if limit else 1,
        "totalItems": total,
    }
    return rows, pagination


async def get_indent_by_tracking_no(db: AsyncSession, tracking_no: str) -> ProcIndent:
    result = await db.execute(
        select(ProcIndent).where(ProcIndent.tracking_no == tracking_no)
    )
    indent = result.scalars().first()
    if not indent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indent not found")
    return indent


async def get_indent_detail(
    db: AsyncSession, tracking_no: str
) -> tuple[ProcIndent, list[ProcIndentItem], str | None]:
    """Returns (indent, items, site_name)."""
    indent = await get_indent_by_tracking_no(db, tracking_no)

    # Get items
    result = await db.execute(
        select(ProcIndentItem).where(ProcIndentItem.indent_id == indent.id)
    )
    items = list(result.scalars().all())

    # Get site name
    site_name = indent.site_id
    try:
        site_uuid = uuid.UUID(indent.site_id)
        site = await db.get(Site, site_uuid)
        if site:
            site_name = site.location_name
    except ValueError:
        pass

    return indent, items, site_name


async def get_indent_detail_products(
    db: AsyncSession, items: list[ProcIndentItem]
) -> list[dict]:
    """Build the rich products array for the detail response."""
    product_codes = [i.product_code for i in items if i.product_code]
    vendor_map = {}
    prod_map = {}
    if product_codes:
        result = await db.execute(
            select(ProcProduct, ProcVendor.company_name)
            .join(ProcVendor, ProcProduct.vendor_code == ProcVendor.vendor_code)
            .where(ProcProduct.product_code.in_(product_codes))
        )
        for prod, vendor_name in result.all():
            prod_map[prod.product_code] = prod
            vendor_map[prod.product_code] = vendor_name

    products = []
    for i, item in enumerate(items, start=1):
        prod = prod_map.get(item.product_code) if item.product_code else None
        gst_rate = float(prod.gst_rate) if prod and prod.gst_rate else 0
        rate = float(item.unit_price)
        qty = float(item.quantity)
        amount = rate * qty * (1 + gst_rate / 100)

        products.append({
            "srNo": i,
            "productGroup": prod.category if prod else None,
            "productName": item.product_name,
            "productDescription": f"Code: {item.product_code}" if item.product_code else None,
            "unit": prod.uom if prod else None,
            "vendor": vendor_map.get(item.product_code),
            "quantity": qty,
            "rate": rate,
            "tax": gst_rate,
            "amount": round(amount, 2),
        })

    return products


# --- Legacy helpers (used by other endpoints not yet migrated) ---

async def list_my_indents(db: AsyncSession, user_email: str) -> list[ProcIndent]:
    result = await db.execute(
        select(ProcIndent)
        .where(ProcIndent.requestor_email == user_email)
        .order_by(ProcIndent.created_at.desc())
    )
    return list(result.scalars().all())


async def get_indent(db: AsyncSession, indent_id: str) -> ProcIndent:
    """Look up by UUID (legacy) or tracking_no."""
    # Try tracking_no first
    result = await db.execute(
        select(ProcIndent).where(ProcIndent.tracking_no == indent_id)
    )
    indent = result.scalars().first()
    if indent:
        return indent

    # Fallback to UUID
    try:
        iid = uuid.UUID(indent_id)
        indent = await db.get(ProcIndent, iid)
        if indent:
            return indent
    except ValueError:
        pass

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indent not found")


async def get_indent_with_items(db: AsyncSession, indent_id: str) -> tuple[ProcIndent, list[ProcIndentItem]]:
    indent = await get_indent(db, indent_id)
    result = await db.execute(
        select(ProcIndentItem).where(ProcIndentItem.indent_id == indent.id)
    )
    items = list(result.scalars().all())
    return indent, items


async def update_indent(
    db: AsyncSession, tracking_no: str, data: IndentUpdate
) -> ProcIndent:
    indent = await get_indent_by_tracking_no(db, tracking_no)

    if indent.status not in ("PENDING_PH_APPROVAL", "PENDING_RM_APPROVAL"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot edit indent in status {indent.status}",
        )

    # Look up products for price
    product_codes = [p.productCode for p in data.products]
    result = await db.execute(
        select(ProcProduct).where(ProcProduct.product_code.in_(product_codes))
    )
    prod_map = {p.product_code: p for p in result.scalars().all()}

    total_value = 0.0
    for item in data.products:
        prod = prod_map.get(item.productCode)
        price = float(prod.final_price) if prod else 0
        total_value += price * item.quantity

    # Update editable fields
    indent.branch_gst = data.branchGst
    indent.request_category = data.requestCategory
    indent.narration = data.narration
    indent.total_value = total_value
    indent.updated_at = datetime.now(IST)

    # Replace items
    existing_items = await db.execute(
        select(ProcIndentItem).where(ProcIndentItem.indent_id == indent.id)
    )
    for item in existing_items.scalars().all():
        await db.delete(item)

    for item in data.products:
        prod = prod_map.get(item.productCode)
        unit_price = float(prod.final_price) if prod else 0
        db.add(ProcIndentItem(
            indent_id=indent.id,
            product_code=item.productCode,
            product_name=prod.product_name if prod else item.productCode,
            quantity=item.quantity,
            unit_price=unit_price,
            total_price=unit_price * item.quantity,
        ))

    await db.commit()
    await db.refresh(indent)
    return indent


async def _next_po_number(db: AsyncSession) -> str:
    count = await db.scalar(select(func.count()).select_from(ProcPurchaseOrder)) or 0
    return f"PO{count + 1:07d}"


async def _create_pos_for_indent(db: AsyncSession, indent: ProcIndent) -> list[str]:
    """Auto-create POs grouped by vendor for a PH-approved indent. Returns PO numbers."""
    # Get indent items
    result = await db.execute(
        select(ProcIndentItem).where(ProcIndentItem.indent_id == indent.id)
    )
    items = list(result.scalars().all())
    if not items:
        return []

    # Group items by vendor_code (look up product → vendor)
    product_codes = [i.product_code for i in items if i.product_code]
    prod_map = {}
    if product_codes:
        result = await db.execute(
            select(ProcProduct).where(ProcProduct.product_code.in_(product_codes))
        )
        prod_map = {p.product_code: p for p in result.scalars().all()}

    vendor_groups: dict[str, list[ProcIndentItem]] = {}
    for item in items:
        prod = prod_map.get(item.product_code) if item.product_code else None
        vendor_code = prod.vendor_code if prod else "UNKNOWN"
        vendor_groups.setdefault(vendor_code, []).append(item)

    now = datetime.now(IST)
    po_numbers = []

    for vendor_code, vendor_items in vendor_groups.items():
        po_number = await _next_po_number(db)
        total_value = sum(float(i.total_price) for i in vendor_items)

        # Calculate expected delivery from max product delivery_days
        max_days = 7  # default
        for item in vendor_items:
            prod = prod_map.get(item.product_code) if item.product_code else None
            if prod and prod.delivery_days and prod.delivery_days > max_days:
                max_days = prod.delivery_days

        from datetime import timedelta
        expected = (now + timedelta(days=max_days)).date()

        po = ProcPurchaseOrder(
            po_number=po_number,
            indent_id=indent.id,
            vendor_code=vendor_code,
            site_id=indent.site_id,
            po_date=now,
            expected_delivery_date=expected,
            tat=max_days,
            tat_status="On Time",
            status="Not Delivered",
            total_value=total_value,
        )
        db.add(po)
        await db.flush()

        for item in vendor_items:
            db.add(ProcPoItem(
                po_id=po.id,
                item_id=str(item.id),
                product_code=item.product_code,
                product_name=item.product_name,
                quantity=float(item.quantity),
                landed_price=float(item.unit_price),
                total_amount=float(item.total_price),
            ))

        po_numbers.append(po_number)

    return po_numbers


async def approve_indent(
    db: AsyncSession, data: ApproveIndentRequest, approved_by: str
) -> list[dict]:
    """Returns list of dicts with trackingNo, status, and poNumbers (if POs were created)."""
    results = []
    for tracking_no in data.indentIds:
        indent = await get_indent_by_tracking_no(db, tracking_no)
        if indent.status not in ("PENDING_PH_APPROVAL", "PENDING_RM_APPROVAL"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot approve indent {tracking_no} in status {indent.status}",
            )

        po_numbers = []
        if indent.status == "PENDING_RM_APPROVAL":
            indent.status = "PENDING_PH_APPROVAL"
        else:
            # PH approval → auto-create POs
            po_numbers = await _create_pos_for_indent(db, indent)
            indent.status = "PO_CREATED"

        indent.approved_by = approved_by
        indent.updated_at = datetime.now(IST)
        results.append({
            "trackingNo": indent.tracking_no,
            "status": indent.status,
            "poNumbers": po_numbers,
        })

    await db.commit()
    return results


async def reject_indent(
    db: AsyncSession, tracking_no: str, data: RejectIndentRequest, rejected_by: str
) -> ProcIndent:
    indent = await get_indent_by_tracking_no(db, tracking_no)
    if indent.status not in ("PENDING_PH_APPROVAL", "PENDING_RM_APPROVAL"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot reject indent in status {indent.status}",
        )
    indent.status = "REJECTED_BY_PH" if indent.status == "PENDING_PH_APPROVAL" else "REJECTED_BY_RM"
    indent.rejection_reason = data.reason
    indent.rejected_by = rejected_by
    indent.updated_at = datetime.now(IST)
    await db.commit()
    await db.refresh(indent)
    return indent
