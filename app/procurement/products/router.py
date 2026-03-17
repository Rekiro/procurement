from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.procurement.products import service
from app.procurement.products.schemas import (
    ProductCreate, ProductResponse, ProductListItem, MarginResponse,
    ApproveProductRequest, RejectProductRequest,
    PriceChangeRequestCreate, PriceChangeRequestResponse,
    ApprovePriceChangeRequest, RejectPriceChangeRequest,
)
from app.procurement.sites.schemas import CatalogProduct, CatalogFilterOptions, FilterOption

# Registered at /api/procurement/products
router = APIRouter()

# Registered at /api/procurement  (for /vendor/products)
vendor_router = APIRouter()


# --- Product submission & management ---

@router.post("", response_model=ApiResponse, status_code=201)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    product = await service.create_product(db, data)
    return success_response(ProductResponse.from_orm(product).model_dump())


@router.get("", response_model=ApiResponse)
async def list_products(
    status: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    rows, pagination = await service.list_products(db, status_filter=status, search=search, page=page, limit=limit)
    return success_response({
        "pagination": pagination,
        "products": [
            ProductListItem(
                productCode=p.product_code,
                productName=p.product_name,
                vendor=vendor_name,
                category=p.category,
                subcategory=p.subcategory,
                price=float(p.price),
                hsnCode=p.hsn_code,
                isTaxExempt=p.is_tax_exempt,
                gstRate=float(p.gst_rate),
                uom=p.uom,
                deliveryDays=p.delivery_days,
                costOfDelivery=float(p.delivery_cost),
                description=p.description,
                status=p.status,
            ).model_dump()
            for p, vendor_name in rows
        ],
    })


@router.post("/approve", response_model=ApiResponse)
async def approve_products(
    data: ApproveProductRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    products = await service.approve_products(db, data, reviewed_by=user.sub)
    return success_response([ProductResponse.from_orm(p).model_dump() for p in products])


@router.post("/{product_code}/reject", response_model=ApiResponse)
async def reject_product(
    product_code: str,
    data: RejectProductRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    product = await service.reject_product(db, product_code, data, reviewed_by=user.sub)
    return success_response(ProductResponse.from_orm(product).model_dump())


@router.get("/catalog", response_model=ApiResponse)
async def get_catalog(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    rows = await service.get_product_catalog(db)

    seen_categories: dict[str, bool] = {}
    seen_brands: dict[str, bool] = {}
    products_list = []

    for product, vendor_name in rows:
        if product.category and product.category not in seen_categories:
            seen_categories[product.category] = True
        brand = vendor_name or "N/A"
        if brand not in seen_brands:
            seen_brands[brand] = True

        products_list.append(CatalogProduct(
            periodFrom=None,
            vendorName=vendor_name or "",
            productCode=product.product_code,
            productName=product.product_name,
            landedPrice=float(product.final_price),
            manufacturedBy=None,
            brandName=None,
            hsnCode=product.hsn_code,
            packaging=product.uom,
            usedFor=None,
            category=product.category,
            lifeCycleDays=None,
            costOfTransportationPerKM=float(product.delivery_cost) if product.delivery_cost else None,
            orderLeadTimeDays=product.delivery_days,
            deliveryBy=None,
            netProductCostPerDay=None,
            gstSetOffAvailable=(float(product.gst_rate) > 0),
            financeTreatment=None,
        ).model_dump())

    return success_response({
        "filterOptions": {
            "categories": [{"value": c, "label": c} for c in seen_categories],
            "brands": [{"value": b, "label": b} for b in seen_brands],
        },
        "products": products_list,
    })


@router.delete("/{product_code}", response_model=ApiResponse)
async def delete_product(
    product_code: str,
    vendor_code: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    await service.delete_product(db, product_code, vendor_code)
    return success_response({"message": "Product deleted"})


# --- Price change requests ---

@router.post("/price-change-requests", response_model=ApiResponse, status_code=201)
async def create_price_change_request(
    data: PriceChangeRequestCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    pcr = await service.create_price_change_request(db, data)
    return success_response(PriceChangeRequestResponse.from_orm(pcr).model_dump())


@router.get("/price-change-requests", response_model=ApiResponse)
async def list_price_change_requests(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    requests = await service.list_price_change_requests(db)
    return success_response([PriceChangeRequestResponse.from_orm(r).model_dump() for r in requests])


@router.post("/price-change-requests/approve", response_model=ApiResponse)
async def approve_price_change_request(
    data: ApprovePriceChangeRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    pcr = await service.approve_price_change_request(db, data, reviewed_by=user.sub)
    return success_response(PriceChangeRequestResponse.from_orm(pcr).model_dump())


@router.post("/price-change-requests/{approval_id}/reject", response_model=ApiResponse)
async def reject_price_change_request(
    approval_id: int,
    data: RejectPriceChangeRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    pcr = await service.reject_price_change_request(db, approval_id, data, reviewed_by=user.sub)
    return success_response(PriceChangeRequestResponse.from_orm(pcr).model_dump())


# --- Margins ---

@router.get("/margins", response_model=ApiResponse)
async def get_margins(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    products = await service.get_margins(db)
    return success_response([MarginResponse.from_orm(p).model_dump() for p in products])


@router.get("/margins/export-template")
async def export_margins_template(
    user: TokenPayload = Depends(get_current_user),
):
    return service.get_margin_template()


@router.post("/margins/bulk-upload", response_model=ApiResponse)
async def bulk_upload_margins(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    file_bytes = await file.read()
    result = await service.bulk_upload_margins(db, file_bytes, file.filename, reviewed_by=user.sub)
    return success_response(result)


@router.get("/bulk-upload-template")
async def get_bulk_upload_template(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    return await service.get_product_bulk_upload_template(db)


@router.post("/bulk-upload", response_model=ApiResponse)
async def bulk_upload_products(
    file: UploadFile = File(...),
    vendor_code: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    file_bytes = await file.read()
    result = await service.bulk_upload_products(db, file_bytes, file.filename, vendor_code)
    return success_response(result)


# --- Vendor's own products (registered at /api/procurement) ---

@vendor_router.get("/vendor/products", response_model=ApiResponse)
async def list_my_products(
    vendor_code: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    products = await service.list_vendor_products(db, vendor_code)
    return success_response([ProductResponse.from_orm(p).model_dump() for p in products])
