import uuid
from datetime import date, datetime

from pydantic import BaseModel


# --- Machinery Requests ---

class MachineryRequestItem(BaseModel):
    machineName: str
    quantity: int
    requestType: str          # new / replacement / additional
    oldAssetId: str | None = None


class MachineryRequestCreate(BaseModel):
    siteId: str
    justification: str
    items: list[MachineryRequestItem]


class MachineryRequestResponse(BaseModel):
    id: uuid.UUID
    requisitionId: str
    siteId: str
    siteManagerEmail: str
    justification: str
    items: list[dict]
    status: str
    rejectionReason: str | None
    createdAt: datetime

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            requisitionId=obj.requisition_id,
            siteId=obj.site_id,
            siteManagerEmail=obj.site_manager_email,
            justification=obj.justification,
            items=obj.items if isinstance(obj.items, list) else [],
            status=obj.status,
            rejectionReason=obj.rejection_reason,
            createdAt=obj.created_at,
        )


# --- Fulfill / Reject ---

class MachineryFulfillItem(BaseModel):
    machineName: str
    quantity: int
    landedPrice: float


class MachineryFulfillRequest(BaseModel):
    vendorId: uuid.UUID
    expectedDeliveryDate: date | None = None
    region: str | None = None
    items: list[MachineryFulfillItem]


class MachineryRejectRequest(BaseModel):
    rejectionReason: str


# --- Machinery Purchase Orders ---

class MachineryPoUpdateRequest(BaseModel):
    status: str | None = None
    deliveryType: str | None = None
    courierName: str | None = None
    podNumber: str | None = None


class MachineryPoResponse(BaseModel):
    id: uuid.UUID
    poNumber: str
    machineryRequestId: uuid.UUID | None
    vendorId: uuid.UUID | None
    vendorName: str | None
    siteId: str
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
            machineryRequestId=obj.machinery_request_id,
            vendorId=obj.vendor_id,
            vendorName=vendor_name,
            siteId=obj.site_id,
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


# --- Machinery GRN ---

class MachineryGrnCreate(BaseModel):
    comments: str | None = None
    signedDcUrl: str
    assetConditionProofUrl: str
    packagingImages: list[str] = []


class MachineryGrnResponse(BaseModel):
    id: uuid.UUID
    poNumber: str
    requestorEmail: str
    comments: str | None
    signedDcUrl: str
    assetConditionProofUrl: str
    packagingImages: list[str]
    submittedAt: datetime

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            poNumber=obj.po_number,
            requestorEmail=obj.requestor_email,
            comments=obj.comments,
            signedDcUrl=obj.signed_dc_url,
            assetConditionProofUrl=obj.asset_condition_proof_url,
            packagingImages=obj.packaging_images if isinstance(obj.packaging_images, list) else [],
            submittedAt=obj.submitted_at,
        )


# --- Machinery Invoices (stored in proc_invoices with invoice_type="machinery") ---

class MachineryConsolidatedItemsRequest(BaseModel):
    poNumbers: list[str]


class MachineryInvoiceCreate(BaseModel):
    invoiceNo: str
    state: str
    billAmount: float
    billUrl: str
    poNumbers: list[str]


class ApproveInvoiceRequest(BaseModel):
    invoiceId: uuid.UUID


class RejectInvoiceRequest(BaseModel):
    rejectionReason: str
