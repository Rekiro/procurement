import uuid
from datetime import date, datetime

from pydantic import BaseModel


# --- Uniform Requests ---

class UniformItem(BaseModel):
    itemName: str
    size: str
    quantity: int


class UniformRequestCreate(BaseModel):
    employeeCode: str
    employeeName: str
    designation: str
    site: str
    client: str | None = None
    issueType: str          # new / replacement / backfill
    replacingEmployeeCode: str | None = None
    justification: str | None = None
    isEarlyReplacement: bool = False
    items: list[UniformItem]


class UniformRequestResponse(BaseModel):
    id: uuid.UUID
    requestId: str
    employeeCode: str
    employeeName: str
    designation: str
    site: str
    client: str | None
    issueType: str
    isEarlyReplacement: bool
    items: list[dict]
    status: str
    rejectionReason: str | None
    createdAt: datetime

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            requestId=obj.request_id,
            employeeCode=obj.employee_code,
            employeeName=obj.employee_name,
            designation=obj.designation,
            site=obj.site,
            client=obj.client,
            issueType=obj.issue_type,
            isEarlyReplacement=obj.is_early_replacement,
            items=obj.items if isinstance(obj.items, list) else [],
            status=obj.status,
            rejectionReason=obj.rejection_reason,
            createdAt=obj.created_at,
        )


# --- Fulfill / Reject ---

class UniformFulfillItem(BaseModel):
    itemName: str
    size: str
    quantity: int
    landedPrice: float


class UniformFulfillRequest(BaseModel):
    vendorId: uuid.UUID
    expectedDeliveryDate: date | None = None
    region: str | None = None
    items: list[UniformFulfillItem]


class UniformRejectRequest(BaseModel):
    rejectionReason: str


# --- Uniform Purchase Orders ---

class UniformPoUpdateRequest(BaseModel):
    status: str | None = None
    deliveryType: str | None = None
    courierName: str | None = None
    podNumber: str | None = None


class UniformPoResponse(BaseModel):
    id: uuid.UUID
    poNumber: str
    uniformRequestId: uuid.UUID | None
    vendorId: uuid.UUID | None
    vendorName: str | None
    employeeName: str
    employeeCode: str
    siteName: str
    region: str | None
    status: str
    items: list[dict]
    poDate: datetime
    expectedDeliveryDate: datetime | None
    deliveryType: str | None
    courierName: str | None
    podNumber: str | None
    dateOfDelivery: datetime | None
    createdAt: datetime

    @classmethod
    def from_orm(cls, obj, vendor_name=None):
        return cls(
            id=obj.id,
            poNumber=obj.po_number,
            uniformRequestId=obj.uniform_request_id,
            vendorId=obj.vendor_id,
            vendorName=vendor_name,
            employeeName=obj.employee_name,
            employeeCode=obj.employee_code,
            siteName=obj.site_name,
            region=obj.region,
            status=obj.status,
            items=obj.items if isinstance(obj.items, list) else [],
            poDate=obj.po_date,
            expectedDeliveryDate=obj.expected_delivery_date,
            deliveryType=obj.delivery_type,
            courierName=obj.courier_name,
            podNumber=obj.pod_number,
            dateOfDelivery=obj.date_of_delivery,
            createdAt=obj.created_at,
        )


# --- GRN (no separate table — updates PO) ---

class UniformGrnCreate(BaseModel):
    signedDcUrl: str
    comments: str | None = None


# --- Consolidated items + invoice ---

class UniformConsolidatedItemsRequest(BaseModel):
    poNumbers: list[str]


class UniformInvoiceCreate(BaseModel):
    invoiceNo: str
    state: str
    billAmount: float
    billUrl: str
    poNumbers: list[str]


class ApproveInvoiceRequest(BaseModel):
    invoiceId: uuid.UUID


class RejectInvoiceRequest(BaseModel):
    rejectionReason: str
