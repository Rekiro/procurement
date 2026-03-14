import uuid
from datetime import datetime

from pydantic import BaseModel


class CashPurchaseProductItem(BaseModel):
    productName: str
    quantity: float
    cost: float


class CashPurchaseCreate(BaseModel):
    siteId: str
    forTheMonth: str          # "YYYY-MM"
    vendorName: str | None = None
    gstNo: str | None = None
    products: list[CashPurchaseProductItem]
    totalCost: float
    billUrl: str


class CashPurchaseResponse(BaseModel):
    id: uuid.UUID
    purchaseId: str
    requestorEmail: str
    siteId: str
    forTheMonth: str
    vendorName: str | None
    gstNo: str | None
    products: list[dict]
    totalCost: float
    billUrl: str
    status: str
    rejectionReason: str | None
    createdAt: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            purchaseId=obj.purchase_id,
            requestorEmail=obj.requestor_email,
            siteId=obj.site_id,
            forTheMonth=obj.for_the_month.strftime("%Y-%m"),
            vendorName=obj.vendor_name,
            gstNo=obj.gst_no,
            products=obj.products if isinstance(obj.products, list) else [],
            totalCost=float(obj.total_cost),
            billUrl=obj.bill_url,
            status=obj.status,
            rejectionReason=obj.rejection_reason,
            createdAt=obj.created_at,
        )


class ApproveCashPurchaseRequest(BaseModel):
    purchaseId: uuid.UUID


class RejectCashPurchaseRequest(BaseModel):
    rejectionReason: str
