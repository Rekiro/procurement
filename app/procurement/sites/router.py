from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenPayload
from app.shared.schemas import ApiResponse, success_response
from app.procurement.sites import service
from app.procurement.sites.schemas import (
    SiteOption, UserSiteItem,
    SiteDetails, CatalogFilterOptions, FilterOption, CatalogProduct, MaterialCatalogResponse,
    SiteOrderHistoryItem, SitePoHistoryItem, SiteIndentHistoryItem,
)

router = APIRouter()


@router.get("/sites/options", response_model=ApiResponse)
async def get_site_options(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    sites = await service.get_site_options(db)
    return success_response([
        SiteOption(siteId=str(s.id), siteName=s.location_name, city=s.city, state=s.state).model_dump()
        for s in sites
    ])


@router.get("/user-sites", response_model=ApiResponse)
async def get_user_sites(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    sites = await service.get_user_sites(db, user.sub)
    return success_response([
        UserSiteItem(siteId=str(s.id), siteName=s.location_name).model_dump()
        for s in sites
    ])


@router.get("/sites/{site_id}/material-catalog", response_model=ApiResponse)
async def get_site_material_catalog(
    site_id: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    site = await service.get_site(db, site_id)
    site_name = site.location_name if site else site_id

    rows = await service.get_site_material_catalog(db, site_id)

    # Build filter options from actual product data
    seen_categories: dict[str, bool] = {}
    seen_brands: dict[str, bool] = {}
    catalog_products = []

    for product, vendor_name in rows:
        cat = product.category
        if cat and cat not in seen_categories:
            seen_categories[cat] = True

        # No brand field in DB yet — use vendor_name as brand proxy
        brand = vendor_name or "N/A"
        if brand not in seen_brands:
            seen_brands[brand] = True

        # netProductCostPerDay: finalPrice / lifeCycleDays (if available; we don't store lifeCycleDays)
        net_cost_per_day = None

        catalog_products.append(CatalogProduct(
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
            netProductCostPerDay=net_cost_per_day,
            gstSetOffAvailable=(float(product.gst_rate) > 0),
            financeTreatment=None,
        ).model_dump())

    response = MaterialCatalogResponse(
        siteDetails=SiteDetails(
            siteId=site_id,
            siteName=site_name,
            budget=None,    # budget tracking not yet implemented
            balance=None,
        ),
        filterOptions=CatalogFilterOptions(
            categories=[FilterOption(value=c, label=c) for c in seen_categories],
            brands=[FilterOption(value=b, label=b) for b in seen_brands],
        ),
        products=catalog_products,
    )
    return success_response(response.model_dump())


@router.get("/sites/{site_id}/history", response_model=ApiResponse)
async def get_site_history(
    site_id: str,
    month: str | None = Query(None, description="Filter by month, e.g. 2025-09"),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Spec #8.6: Site Order History — returns indent history for the site."""
    indents = await service.get_site_indent_history(db, site_id, month=month)
    return success_response([
        SiteOrderHistoryItem(
            siteId=i.site_id,
            trackingNo=i.tracking_no,
            requestDate=i.created_at.strftime("%Y-%m-%d"),
            siteBudget=None,    # budget tracking not yet implemented
            value=float(i.total_value),
            status=i.status,
            balance=None,
        ).model_dump()
        for i in indents
    ])


@router.get("/sites/{site_id}/indent-history", response_model=ApiResponse)
async def get_site_indent_history(
    site_id: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    indents = await service.get_site_indent_history(db, site_id)
    return success_response([
        SiteIndentHistoryItem(
            id=i.id,
            trackingNo=i.tracking_no,
            requestorEmail=i.requestor_email,
            forMonth=i.for_month,
            category=i.category,
            status=i.status,
            totalValue=float(i.total_value),
            createdAt=i.created_at,
        ).model_dump()
        for i in indents
    ])
