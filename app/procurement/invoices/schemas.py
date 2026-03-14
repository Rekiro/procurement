import uuid
from datetime import datetime

from pydantic import BaseModel


class InvoiceCreate(BaseModel):
    invoiceNo: str
    invoiceType: str   # material / machinery / uniform
    state: str
    billAmount: float
    billUrl: str
    poNumbers: list[str]


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoiceId: str
    vendorId: uuid.UUID | None
    invoiceNo: str
    invoiceType: str
    state: str
    billAmount: float
    billUrl: str
    status: str
    rejectionReason: str | None
    poNumbers: list[str]
    submittedAt: datetime
    reviewedAt: datetime | None
    reviewedBy: str | None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj, po_numbers=None):
        return cls(
            id=obj.id,
            invoiceId=obj.invoice_id,
            vendorId=obj.vendor_id,
            invoiceNo=obj.invoice_no,
            invoiceType=obj.invoice_type,
            state=obj.state,
            billAmount=float(obj.bill_amount),
            billUrl=obj.bill_url,
            status=obj.status,
            rejectionReason=obj.rejection_reason,
            poNumbers=po_numbers or [],
            submittedAt=obj.submitted_at,
            reviewedAt=obj.reviewed_at,
            reviewedBy=obj.reviewed_by,
        )


class ApproveInvoiceRequest(BaseModel):
    invoiceId: uuid.UUID


class RejectInvoiceRequest(BaseModel):
    rejectionReason: str
