from datetime import datetime

from pydantic import BaseModel, Field


class CashPurchaseProductItem(BaseModel):
    productName: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    cost: float = Field(..., gt=0)


class CashPurchaseCreate(BaseModel):
    requestorEmail: str = Field(..., min_length=1)
    siteId: str = Field(..., min_length=1)
    forTheMonth: str = Field(..., min_length=1)
    vendorName: str | None = None
    gstNo: str | None = None
    products: list[CashPurchaseProductItem] = Field(..., min_length=1)


class CashPurchaseListItem(BaseModel):
    purchaseId: str
    requesterName: str
    requestDate: str
    forTheMonth: str           # "Month YYYY"
    site: str
    vendorName: str | None
    gstNo: str | None
    billUrl: str
    products: list[dict]
    totalValue: float
    status: str


class ApproveCashPurchaseRequest(BaseModel):
    purchaseIds: list[str] = Field(..., min_length=1)


class RejectCashPurchaseRequest(BaseModel):
    reason: str = Field(..., min_length=1)
