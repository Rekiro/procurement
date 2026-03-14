import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.procurement.invoices.models import ProcInvoice, ProcInvoicePoLink
from app.procurement.invoices.schemas import InvoiceCreate, ApproveInvoiceRequest, RejectInvoiceRequest
from app.procurement.vendors.models import ProcVendor
from app.procurement.purchase_orders.models import ProcPurchaseOrder


async def submit_invoice(db: AsyncSession, data: InvoiceCreate, vendor_email: str):
    vendor = await db.scalar(select(ProcVendor).where(ProcVendor.email == vendor_email))

    count = await db.scalar(select(func.count()).select_from(ProcInvoice))
    invoice_id = f"INV-{(count or 0) + 1:06d}"

    invoice = ProcInvoice(
        invoice_id=invoice_id,
        vendor_id=vendor.id if vendor else None,
        invoice_no=data.invoiceNo,
        invoice_type=data.invoiceType,
        state=data.state,
        bill_amount=data.billAmount,
        bill_url=data.billUrl,
    )
    db.add(invoice)
    await db.flush()

    for po_number in data.poNumbers:
        db.add(ProcInvoicePoLink(invoice_id=invoice.id, po_number=po_number))
        po = await db.scalar(
            select(ProcPurchaseOrder).where(ProcPurchaseOrder.po_number == po_number)
        )
        if po:
            po.status = "INVOICE_SUBMITTED"
            po.updated_at = datetime.now(timezone.utc)

    await db.commit()
    return invoice, data.poNumbers


async def list_invoices(db: AsyncSession, status_filter: str | None = None):
    q = select(ProcInvoice).order_by(ProcInvoice.submitted_at.desc())
    if status_filter:
        q = q.where(ProcInvoice.status == status_filter)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_invoice_po_numbers(db: AsyncSession, invoice_id: uuid.UUID) -> list[str]:
    result = await db.execute(
        select(ProcInvoicePoLink).where(ProcInvoicePoLink.invoice_id == invoice_id)
    )
    return [link.po_number for link in result.scalars().all()]


async def approve_invoice(db: AsyncSession, data: ApproveInvoiceRequest, reviewed_by: str):
    invoice = await db.get(ProcInvoice, data.invoiceId)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.status != "Pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invoice is not in Pending status")

    invoice.status = "Approved"
    invoice.reviewed_at = datetime.now(timezone.utc)
    invoice.reviewed_by = reviewed_by
    await db.commit()
    await db.refresh(invoice)
    return invoice


async def reject_invoice(db: AsyncSession, invoice_id: uuid.UUID, data: RejectInvoiceRequest,
                         reviewed_by: str):
    invoice = await db.get(ProcInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if invoice.status != "Pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invoice is not in Pending status")

    invoice.status = "Rejected"
    invoice.rejection_reason = data.rejectionReason
    invoice.reviewed_at = datetime.now(timezone.utc)
    invoice.reviewed_by = reviewed_by
    await db.commit()
    await db.refresh(invoice)
    return invoice
