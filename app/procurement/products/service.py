import io
import math
from datetime import datetime, timezone, date

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.products.models import ProcProduct, ProcProductPriceChangeRequest
from app.procurement.vendors.models import ProcVendor
from app.procurement.products.schemas import (
    ProductCreate, ApproveProductRequest, RejectProductRequest,
    PriceChangeRequestCreate, ApprovePriceChangeRequest, RejectPriceChangeRequest,
)
from app.shared.excel_utils import create_template_workbook, workbook_to_streaming_response, parse_upload_to_rows


def _calculate_final_price(price: float, margin_pct: float | None, margin_amt: float | None) -> float:
    if margin_pct is not None:
        return round(price * (1 + margin_pct / 100), 2)
    if margin_amt is not None:
        return round(price + margin_amt, 2)
    return price


async def _get_vendor_by_code(db: AsyncSession, vendor_code: str) -> ProcVendor:
    vendor = await db.get(ProcVendor, vendor_code)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vendor {vendor_code} not found")
    if vendor.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor account is not active")
    return vendor


async def _next_product_code(db: AsyncSession) -> str:
    count = await db.scalar(select(func.count()).select_from(ProcProduct))
    return f"PRD{(count or 0) + 1:07d}"


async def create_product(db: AsyncSession, data: ProductCreate) -> ProcProduct:
    vendor = await _get_vendor_by_code(db, data.vendorCode)
    product_code = await _next_product_code(db)

    product = ProcProduct(
        product_code=product_code,
        vendor_code=vendor.vendor_code,
        product_name=data.productName,
        category=data.category,
        subcategory=data.subcategory,
        price=data.price,
        hsn_code=data.hsnCode,
        is_tax_exempt=data.isTaxExempt,
        gst_rate=0.0 if data.isTaxExempt else data.gstRate,
        delivery_days=data.deliveryDays,
        delivery_cost=data.deliveryCost,
        uom=data.uom,
        description=data.description,
        final_price=data.price,   # no margin set yet
        status="Pending",
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def list_products(
    db: AsyncSession,
    status_filter: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[tuple], dict]:
    """Returns (list of (ProcProduct, vendor_name) tuples, pagination dict)."""
    q = (
        select(ProcProduct, ProcVendor.company_name)
        .join(ProcVendor, ProcProduct.vendor_code == ProcVendor.vendor_code)
        .order_by(ProcProduct.created_at.desc())
    )
    if status_filter:
        q = q.where(ProcProduct.status == status_filter)
    if search:
        q = q.where(ProcProduct.product_name.ilike(f"%{search}%"))

    # Manual pagination (paginate() helper uses .scalars() which strips tuples)
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


async def approve_products(db: AsyncSession, data: ApproveProductRequest, reviewed_by: str) -> list[ProcProduct]:
    approved = []
    for product_code in data.productIds:
        product = await db.get(ProcProduct, product_code)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_code} not found")
        if product.status != "Pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Product {product_code} is already {product.status}")
        product.status = "Approved"
        product.updated_at = datetime.now(timezone.utc)
        approved.append(product)

    await db.commit()
    for p in approved:
        await db.refresh(p)
    return approved


async def reject_product(db: AsyncSession, product_code: str, data: RejectProductRequest, reviewed_by: str) -> ProcProduct:
    product = await db.get(ProcProduct, product_code)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product.status = "Rejected"
    product.rejection_reason = data.reason
    product.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(product)
    return product


async def get_product_catalog(db: AsyncSession) -> list[tuple]:
    result = await db.execute(
        select(ProcProduct, ProcVendor.company_name)
        .join(ProcVendor, ProcProduct.vendor_code == ProcVendor.vendor_code)
        .where(ProcProduct.status == "Approved")
        .order_by(ProcProduct.product_name)
    )
    return list(result.all())


async def list_vendor_products(db: AsyncSession, vendor_code: str) -> list[ProcProduct]:
    result = await db.execute(
        select(ProcProduct).where(ProcProduct.vendor_code == vendor_code).order_by(ProcProduct.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_product(db: AsyncSession, product_code: str, vendor_code: str) -> None:
    product = await db.get(ProcProduct, product_code)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.vendor_code != vendor_code:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't own this product")

    await db.delete(product)
    await db.commit()


async def create_price_change_request(db: AsyncSession, data: PriceChangeRequestCreate) -> ProcProductPriceChangeRequest:
    vendor = await _get_vendor_by_code(db, data.vendorCode)

    if data.wefDate <= date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="WEF date must be a future date")

    product = await db.get(ProcProduct, data.productCode)
    if not product or product.vendor_code != vendor.vendor_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or not owned by vendor")

    pcr = ProcProductPriceChangeRequest(
        product_code=data.productCode,
        vendor_code=vendor.vendor_code,
        new_price=data.newPrice,
        wef_date=data.wefDate,
        status="Pending",
    )
    db.add(pcr)
    await db.commit()
    await db.refresh(pcr)
    return pcr


async def list_price_change_requests(db: AsyncSession) -> list[ProcProductPriceChangeRequest]:
    result = await db.execute(
        select(ProcProductPriceChangeRequest).order_by(ProcProductPriceChangeRequest.created_at.desc())
    )
    return list(result.scalars().all())


async def approve_price_change_request(db: AsyncSession, data: ApprovePriceChangeRequest, reviewed_by: str) -> ProcProductPriceChangeRequest:
    pcr = await db.get(ProcProductPriceChangeRequest, data.approvalId)
    if not pcr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price change request not found")
    if pcr.status != "Pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Request is already {pcr.status}")

    # Update product price
    product = await db.get(ProcProduct, pcr.product_code)
    if product:
        product.price = pcr.new_price
        product.final_price = _calculate_final_price(float(pcr.new_price), float(product.margin_percentage) if product.margin_percentage else None, float(product.direct_margin_amount) if product.direct_margin_amount else None)
        product.updated_at = datetime.now(timezone.utc)

    pcr.status = "Approved"
    pcr.reviewed_at = datetime.now(timezone.utc)
    pcr.reviewed_by = reviewed_by
    await db.commit()
    await db.refresh(pcr)
    return pcr


async def reject_price_change_request(db: AsyncSession, approval_id: int, data: RejectPriceChangeRequest, reviewed_by: str) -> ProcProductPriceChangeRequest:
    pcr = await db.get(ProcProductPriceChangeRequest, approval_id)
    if not pcr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price change request not found")

    pcr.status = "Rejected"
    pcr.rejection_reason = data.reason
    pcr.reviewed_at = datetime.now(timezone.utc)
    pcr.reviewed_by = reviewed_by
    await db.commit()
    await db.refresh(pcr)
    return pcr


async def get_margins(db: AsyncSession) -> list[ProcProduct]:
    result = await db.execute(
        select(ProcProduct).where(ProcProduct.status == "Approved").order_by(ProcProduct.product_name)
    )
    return list(result.scalars().all())


def get_margin_template():
    from app.shared.excel_utils import create_template_workbook, workbook_to_streaming_response
    wb = create_template_workbook(["productCode", "marginPercentage", "directMarginAmount"])
    return workbook_to_streaming_response(wb, "margins_template.xlsx")


async def get_product_bulk_upload_template(db: AsyncSession):
    # Query distinct categories and subcategories from approved products
    cat_result = await db.execute(
        select(ProcProduct.category).where(ProcProduct.category.isnot(None)).distinct()
    )
    categories = sorted([r[0] for r in cat_result.all() if r[0]])

    subcat_result = await db.execute(
        select(ProcProduct.subcategory).where(ProcProduct.subcategory.isnot(None)).distinct()
    )
    subcategories = sorted([r[0] for r in subcat_result.all() if r[0]])

    headers = [
        "Product Name", "Category", "Sub Category", "Price", "HSN Code",
        "GST Rate (%)", "UOM", "Number of Delivery Days", "Cost of Delivery", "Description",
    ]
    dropdowns = {
        "Category": categories or ["General"],
        "Sub Category": subcategories or ["General"],
        "UOM": ["PCS", "KG", "LTR", "BOX", "MTR", "SET"],
    }
    wb = create_template_workbook(headers, dropdowns)
    return workbook_to_streaming_response(wb, "Product_Upload_Template.xlsx")


async def bulk_upload_margins(db: AsyncSession, file_bytes: bytes, filename: str, reviewed_by: str) -> dict:
    rows = parse_upload_to_rows(file_bytes, filename)
    success, errors = 0, []

    for i, row in enumerate(rows, start=2):
        product_code = str(row.get("productCode", "")).strip()
        if not product_code:
            errors.append({"row": i, "error": "productCode is required"})
            continue

        product = await db.scalar(select(ProcProduct).where(ProcProduct.product_code == product_code))
        if not product:
            errors.append({"row": i, "error": f"Product {product_code} not found"})
            continue

        try:
            margin_pct_raw = row.get("marginPercentage")
            margin_amt_raw = row.get("directMarginAmount")
            margin_pct = float(margin_pct_raw) if margin_pct_raw not in (None, "", "None") else None
            margin_amt = float(margin_amt_raw) if margin_amt_raw not in (None, "", "None") else None

            product.margin_percentage = margin_pct
            product.direct_margin_amount = margin_amt
            product.final_price = _calculate_final_price(float(product.price), margin_pct, margin_amt)
            product.updated_at = datetime.now(timezone.utc)
            success += 1
        except (ValueError, TypeError) as e:
            errors.append({"row": i, "error": str(e)})

    await db.commit()
    return {"totalRows": len(rows), "successCount": success, "failureCount": len(errors), "errors": errors}


async def bulk_upload_products(db: AsyncSession, file_bytes: bytes, filename: str, vendor_code: str) -> dict:
    vendor = await _get_vendor_by_code(db, vendor_code)
    rows = parse_upload_to_rows(file_bytes, filename)
    success, errors = 0, []

    for i, row in enumerate(rows, start=2):
        try:
            product_code = await _next_product_code(db)
            price = float(row.get("Price", 0))
            product = ProcProduct(
                product_code=product_code,
                vendor_code=vendor.vendor_code,
                product_name=str(row.get("Product Name", "")).strip(),
                category=str(row.get("Category", "")).strip(),
                subcategory=str(row.get("Sub Category", "")).strip(),
                price=price,
                hsn_code=str(row.get("HSN Code", "")).strip(),
                is_tax_exempt=False,
                gst_rate=float(row.get("GST Rate (%)", 0)),
                delivery_days=int(row.get("Number of Delivery Days", 1)),
                delivery_cost=float(row.get("Cost of Delivery", 0)),
                uom=str(row.get("UOM", "PCS")).strip(),
                description=str(row.get("Description", "")).strip() or None,
                final_price=price,
                status="Pending",
            )
            db.add(product)
            await db.flush()
            success += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    await db.commit()
    return {"totalRows": len(rows), "successCount": success, "failureCount": len(errors), "errors": errors}
