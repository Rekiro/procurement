from datetime import datetime

from pydantic import BaseModel


# --- Invoice Submit (parsed from multipart 'data' JSON string) ---

class InvoiceSubmitData(BaseModel):
    poNumbers: list[str]
    invoiceNo: str
    state: str
    billAmount: float


# --- Approve / Reject ---

class ApproveInvoiceRequest(BaseModel):
    invoiceIds: list[str]


class RejectInvoiceRequest(BaseModel):
    reason: str


# --- Response ---

class InvoiceResponse(BaseModel):
    invoiceId: str
    invoiceNo: str
    invoiceDate: datetime
    billAmount: float
    state: str
    billUrl: str
    status: str
    reason: str | None
    poNumbers: list[str]
    reviewedAt: datetime | None
    reviewedBy: str | None

    @classmethod
    def from_orm(cls, obj, po_numbers=None):
        return cls(
            invoiceId=obj.invoice_id,
            invoiceNo=obj.invoice_no,
            invoiceDate=obj.submitted_at,
            billAmount=float(obj.bill_amount),
            state=obj.state,
            billUrl=obj.bill_url,
            status=obj.status,
            reason=obj.rejection_reason,
            poNumbers=po_numbers or [],
            reviewedAt=obj.reviewed_at,
            reviewedBy=obj.reviewed_by,
        )
