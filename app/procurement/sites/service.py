from sqlalchemy import select, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.sites.models import Site
from app.procurement.products.models import ProcProduct
from app.procurement.vendors.models import ProcVendor
from app.procurement.purchase_orders.models import ProcPurchaseOrder
from app.procurement.indents.models import ProcIndent


async def get_site_options(db: AsyncSession) -> list[Site]:
    result = await db.execute(select(Site).order_by(Site.location_name))
    return list(result.scalars().all())


async def get_user_sites(db: AsyncSession, user_email: str) -> list[Site]:
    """
    Returns all sites (unfiltered).

    BLOCKED: The spec says this should return only sites assigned to the
    logged-in requestor, but two prerequisites are missing:
      1. Real per-user auth (currently single shared credential — see CLAUDE.md).
      2. A user-site assignment table. Neither the commercial app's `sites`
         table nor any procurement table has a user↔site mapping. The
         commercial team would need to provide this (or we create one here).
    Until both are resolved, return all sites.
    """
    result = await db.execute(select(Site).order_by(Site.location_name))
    return list(result.scalars().all())


async def get_site(db: AsyncSession, site_id: str) -> Site | None:
    import uuid as _uuid
    try:
        site_uuid = _uuid.UUID(site_id)
    except ValueError:
        return None
    return await db.get(Site, site_uuid)


async def get_site_material_catalog(db: AsyncSession, site_id: str) -> list[tuple[ProcProduct, str]]:
    """
    Returns (product, vendor_name) tuples for all approved products.
    Products are not site-specific — all Approved products are available everywhere.
    """
    result = await db.execute(
        select(ProcProduct, ProcVendor.company_name)
        .join(ProcVendor, ProcProduct.vendor_code == ProcVendor.vendor_code)
        .where(ProcProduct.status == "Approved")
        .order_by(ProcProduct.category, ProcProduct.product_name)
    )
    return list(result.all())


async def get_site_history(db: AsyncSession, site_id: str) -> list[ProcPurchaseOrder]:
    result = await db.execute(
        select(ProcPurchaseOrder)
        .where(ProcPurchaseOrder.site_id == site_id)
        .order_by(ProcPurchaseOrder.po_date.desc())
    )
    return list(result.scalars().all())


async def get_site_indent_history(
    db: AsyncSession, site_id: str, month: str | None = None,
) -> list[ProcIndent]:
    """
    Get indent history for a site.
    month: optional "YYYY-MM" filter (matches against created_at).
    """
    q = (
        select(ProcIndent)
        .where(ProcIndent.site_id == site_id)
        .order_by(ProcIndent.created_at.desc())
    )
    if month:
        parts = month.split("-")
        if len(parts) == 2:
            year, mon = int(parts[0]), int(parts[1])
            q = q.where(
                extract("year", ProcIndent.created_at) == year,
                extract("month", ProcIndent.created_at) == mon,
            )
    result = await db.execute(q)
    return list(result.scalars().all())
