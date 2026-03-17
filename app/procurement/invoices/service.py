import math
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func, or_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.invoices.models import ProcInvoice, ProcInvoicePoLink
from app.procurement.invoices.schemas import InvoiceSubmitData, ApproveInvoiceRequest, RejectInvoiceRequest
from app.procurement.purchase_orders.models import (
    ProcPurchaseOrder, ProcPoItem, ProcGrn, ProcGrnItem, ProcGrnPhoto,
)
from app.procurement.indents.models import ProcIndent


async def _compute_grn_total(db: AsyncSession, po_numbers: list[str]) -> float:
    """Calculate expected billable amount: sum(receivedQuantity × landedPrice) across all GRNs."""
    pos_result = await db.execute(
        select(ProcPurchaseOrder).where(ProcPurchaseOrder.po_number.in_(po_numbers))
    )
    pos = list(pos_result.scalars().all())
    if not pos:
        raise HTTPException(status_code=404, detail=f"PO(s) not found: {', '.join(po_numbers)}")

    po_map = {po.po_number: po for po in pos}
    missing_pos = set(po_numbers) - set(po_map)
    if missing_pos:
        raise HTTPException(status_code=404, detail=f"PO(s) not found: {', '.join(missing_pos)}")

    po_ids = [po.id for po in pos]

    grns_result = await db.execute(
        select(ProcGrn).where(ProcGrn.po_id.in_(po_ids))
    )
    grns = list(grns_result.scalars().all())
    grn_map = {grn.po_id: grn for grn in grns}

    # Check all POs have GRNs
    for po in pos:
        if po.id not in grn_map:
            raise HTTPException(
                status_code=400,
                detail=f"No GRN found for PO {po.po_number}. All POs must have a GRN before submitting an invoice.",
            )

    # Load GRN items
    grn_ids = [grn.id for grn in grns]
    gi_result = await db.execute(select(ProcGrnItem).where(ProcGrnItem.grn_id.in_(grn_ids)))
    grn_items_by_grn: dict[uuid.UUID, list[ProcGrnItem]] = {}
    for item in gi_result.scalars().all():
        grn_items_by_grn.setdefault(item.grn_id, []).append(item)

    # Load PO items (for landed_price lookup)
    pi_result = await db.execute(select(ProcPoItem).where(ProcPoItem.po_id.in_(po_ids)))
    po_item_map: dict[str, float] = {}  # "{po_id}:{item_id}" -> landed_price
    for item in pi_result.scalars().all():
        po_item_map[f"{item.po_id}:{item.item_id}"] = float(item.landed_price)

    total = 0.0
    for po in pos:
        grn = grn_map[po.id]
        for gi in grn_items_by_grn.get(grn.id, []):
            landed = po_item_map.get(f"{po.id}:{gi.item_id}", 0.0)
            total += float(gi.received_quantity) * landed

    return round(total, 2)


async def submit_invoice(db: AsyncSession, data: InvoiceSubmitData, bill_url: str):
    # Validate bill amount against GRN totals
    expected = await _compute_grn_total(db, data.poNumbers)
    submitted = round(data.billAmount, 2)
    if abs(expected - submitted) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invoice submission failed: The provided Bill Amount (₹{submitted:,.2f}) "
                f"does not match the calculated amount based on GRN records (₹{expected:,.2f})."
            ),
        )

    # Derive vendor_code from first PO
    first_po = await db.scalar(
        select(ProcPurchaseOrder).where(ProcPurchaseOrder.po_number == data.poNumbers[0])
    )
    vendor_code = first_po.vendor_code if first_po else None

    count = await db.scalar(select(func.count()).select_from(ProcInvoice))
    invoice_id = f"INV{(count or 0) + 1:07d}"

    invoice = ProcInvoice(
        invoice_id=invoice_id,
        vendor_code=vendor_code,
        invoice_no=data.invoiceNo,
        invoice_type="material",
        state=data.state,
        bill_amount=data.billAmount,
        bill_url=bill_url,
    )
    db.add(invoice)
    await db.flush()

    for po_number in data.poNumbers:
        db.add(ProcInvoicePoLink(invoice_id=invoice.id, po_number=po_number))
        linked_po = await db.scalar(
            select(ProcPurchaseOrder).where(ProcPurchaseOrder.po_number == po_number)
        )
        if linked_po:
            linked_po.status = "INVOICE_SUBMITTED"
            linked_po.updated_at = datetime.now(timezone.utc)

    await db.commit()
    po_numbers = await get_invoice_po_numbers(db, invoice.id)
    return invoice, po_numbers


async def get_invoice_po_numbers(db: AsyncSession, invoice_uuid: uuid.UUID) -> list[str]:
    result = await db.execute(
        select(ProcInvoicePoLink).where(ProcInvoicePoLink.invoice_id == invoice_uuid)
    )
    return [link.po_number for link in result.scalars().all()]


async def list_invoices_paginated(
    db: AsyncSession,
    status_filter: str | None = None,
    search: str | None = None,
    site: str | None = None,
    state: str | None = None,
    vendor_code: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[dict], dict, dict]:
    """Returns (invoices_list, pagination, filter_options)."""
    from sqlalchemy import cast, String
    from app.procurement.sites.models import Site

    q = select(ProcInvoice).order_by(ProcInvoice.submitted_at.desc())

    if status_filter:
        q = q.where(ProcInvoice.status == status_filter)
    if state:
        q = q.where(ProcInvoice.state == state)
    if vendor_code:
        q = q.where(ProcInvoice.vendor_code == vendor_code)
    if site:
        # Filter invoices whose linked POs belong to this site
        site_inv_ids = (
            select(ProcInvoicePoLink.invoice_id)
            .join(ProcPurchaseOrder, ProcInvoicePoLink.po_number == ProcPurchaseOrder.po_number)
            .join(Site, ProcPurchaseOrder.site_id == cast(Site.id, String))
            .where(Site.location_name == site)
        )
        q = q.where(ProcInvoice.id.in_(site_inv_ids))
    if search:
        term = f"%{search}%"
        q = q.where(or_(
            ProcInvoice.invoice_id.ilike(term),
            ProcInvoice.invoice_no.ilike(term),
        ))

    count_q = select(func.count()).select_from(q.subquery())
    total = await db.scalar(count_q) or 0

    offset = (page - 1) * limit
    result = await db.execute(q.offset(offset).limit(limit))
    invoices = list(result.scalars().all())

    if not invoices:
        return [], {
            "currentPage": page,
            "totalPages": 0,
            "totalItems": 0,
        }, {"sites": [], "states": []}

    # Batch load PO links
    invoice_uuids = [inv.id for inv in invoices]
    links_result = await db.execute(
        select(ProcInvoicePoLink).where(ProcInvoicePoLink.invoice_id.in_(invoice_uuids))
    )
    links = list(links_result.scalars().all())
    po_numbers_by_inv: dict[uuid.UUID, list[str]] = {}
    all_po_numbers: set[str] = set()
    for link in links:
        po_numbers_by_inv.setdefault(link.invoice_id, []).append(link.po_number)
        all_po_numbers.add(link.po_number)

    # Batch load POs + indent tracking + site name
    all_po_numbers_list = list(all_po_numbers)
    po_data_map: dict[str, tuple] = {}  # po_number -> (po, tracking_no, site_name)
    if all_po_numbers_list:
        pos_result = await db.execute(
            select(
                ProcPurchaseOrder,
                ProcIndent.tracking_no.label("tracking_no"),
                Site.location_name.label("site_name"),
            )
            .outerjoin(ProcIndent, ProcPurchaseOrder.indent_id == ProcIndent.id)
            .outerjoin(Site, ProcPurchaseOrder.site_id == cast(Site.id, String))
            .where(ProcPurchaseOrder.po_number.in_(all_po_numbers_list))
        )
        for po, tracking_no, site_name in pos_result.all():
            po_data_map[po.po_number] = (po, tracking_no, site_name)

    # Batch load PO items
    po_ids = [po_data_map[pn][0].id for pn in all_po_numbers_list if pn in po_data_map]
    po_items_by_po: dict[uuid.UUID, list[ProcPoItem]] = {}
    if po_ids:
        items_result = await db.execute(
            select(ProcPoItem).where(ProcPoItem.po_id.in_(po_ids))
        )
        for item in items_result.scalars().all():
            po_items_by_po.setdefault(item.po_id, []).append(item)

    # Batch load GRNs
    grn_map: dict[str, ProcGrn] = {}  # po_number -> GRN
    grn_items_map: dict[uuid.UUID, list[ProcGrnItem]] = {}
    grn_photos_map: dict[uuid.UUID, list[str]] = {}
    if all_po_numbers_list:
        grns_result = await db.execute(
            select(ProcGrn).where(ProcGrn.po_number.in_(all_po_numbers_list))
        )
        grns = list(grns_result.scalars().all())
        for grn in grns:
            grn_map[grn.po_number] = grn
        if grns:
            grn_ids = [grn.id for grn in grns]
            gi_result = await db.execute(
                select(ProcGrnItem).where(ProcGrnItem.grn_id.in_(grn_ids))
            )
            for gi in gi_result.scalars().all():
                grn_items_map.setdefault(gi.grn_id, []).append(gi)
            gp_result = await db.execute(
                select(ProcGrnPhoto).where(ProcGrnPhoto.grn_id.in_(grn_ids))
            )
            for gp in gp_result.scalars().all():
                grn_photos_map.setdefault(gp.grn_id, []).append(gp.photo_url)

    # Filter options: distinct states from invoices, distinct sites from linked POs
    states_result = await db.execute(
        select(distinct(ProcInvoice.state)).where(ProcInvoice.state.isnot(None))
    )
    available_states = sorted([r[0] for r in states_result.all() if r[0]])
    available_sites = sorted({
        site_name
        for pn, (_, _, site_name) in po_data_map.items()
        if site_name
    })

    def _fmt_date(d) -> str | None:
        if d is None:
            return None
        if hasattr(d, "strftime"):
            return d.strftime("%Y-%m-%d")
        return str(d)

    invoice_list = []
    for inv in invoices:
        inv_po_numbers = po_numbers_by_inv.get(inv.id, [])

        related_pos = []
        po_items_flat = []
        grn_items_flat = []
        signed_dc_urls = []
        comments_parts = []
        packaging_images = []

        for pn in inv_po_numbers:
            if pn in po_data_map:
                po, tracking_no, site_name = po_data_map[pn]

                related_pos.append({
                    "poNumber": pn,
                    "materialRequestId": tracking_no,
                    "siteName": site_name or po.site_id,
                    "poDate": _fmt_date(po.po_date),
                })

                for item in po_items_by_po.get(po.id, []):
                    po_items_flat.append({
                        "productName": item.product_name,
                        "quantity": float(item.quantity),
                        "rate": float(item.landed_price),
                        "amount": float(item.total_amount),
                    })

            grn = grn_map.get(pn)
            if grn:
                signed_dc_urls.append(grn.signed_dc_url)
                if grn.comments:
                    comments_parts.append(grn.comments)
                for gi in grn_items_map.get(grn.id, []):
                    grn_items_flat.append({
                        "itemId": gi.item_id,
                        "itemName": gi.item_name,
                        "orderedQuantity": float(gi.ordered_quantity),
                        "receivedQuantity": float(gi.received_quantity),
                        "isAccepted": gi.is_accepted,
                    })
                packaging_images.extend(grn_photos_map.get(grn.id, []))

        invoice_list.append({
            "invoiceId": inv.invoice_id,
            "invoiceNo": inv.invoice_no,
            "invoiceDate": inv.submitted_at.isoformat(),
            "billAmount": float(inv.bill_amount),
            "state": inv.state,
            "billUrl": inv.bill_url,
            "status": inv.status,
            "reason": inv.rejection_reason,
            "relatedPurchaseOrders": related_pos,
            "_poItems": po_items_flat,
            "_grnDetails": {
                "items": grn_items_flat,
                "signedDc": signed_dc_urls[0] if signed_dc_urls else None,
                "comments": "; ".join(comments_parts) if comments_parts else None,
                "packagingImages": packaging_images,
            },
        })

    pagination = {
        "currentPage": page,
        "totalPages": math.ceil(total / limit) if limit else 1,
        "totalItems": total,
    }
    filter_opts = {"sites": available_sites, "states": available_states}
    return invoice_list, pagination, filter_opts


async def approve_invoices(db: AsyncSession, invoice_ids: list[str], reviewed_by: str):
    result = await db.execute(
        select(ProcInvoice).where(ProcInvoice.invoice_id.in_(invoice_ids))
    )
    invoices = list(result.scalars().all())

    not_found = set(invoice_ids) - {inv.invoice_id for inv in invoices}
    if not_found:
        raise HTTPException(
            status_code=404,
            detail=f"Invoices not found: {', '.join(sorted(not_found))}",
        )

    approved = []
    for inv in invoices:
        if inv.status != "Pending":
            continue
        inv.status = "Approved"
        inv.reviewed_at = datetime.now(timezone.utc)
        inv.reviewed_by = reviewed_by
        approved.append(inv)

    await db.commit()
    return approved


async def reject_invoice(
    db: AsyncSession, invoice_id: str, data: RejectInvoiceRequest, reviewed_by: str
):
    invoice = await db.scalar(
        select(ProcInvoice).where(ProcInvoice.invoice_id == invoice_id)
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status != "Pending":
        raise HTTPException(status_code=400, detail="Invoice is not in Pending status")

    invoice.status = "Rejected"
    invoice.rejection_reason = data.reason
    invoice.reviewed_at = datetime.now(timezone.utc)
    invoice.reviewed_by = reviewed_by
    await db.commit()
    await db.refresh(invoice)
    return invoice
