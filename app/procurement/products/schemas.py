from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, field_validator


class ProductCreate(BaseModel):
    vendorCode: str
    productName: str
    category: str
    subcategory: str
    price: float
    hsnCode: str
    isTaxExempt: bool = False
    gstRate: float = 0.0
    deliveryDays: int
    deliveryCost: float = 0.0
    uom: str          # PCS/KG/LTR/BOX etc.
    description: str | None = None

    @field_validator("hsnCode")
    @classmethod
    def hsn_must_be_8_digits(cls, v):
        if not v.isdigit() or len(v) != 8:
            raise ValueError("HSN code must be exactly 8 digits")
        return v

    @field_validator("deliveryDays")
    @classmethod
    def delivery_days_positive(cls, v):
        if v < 1:
            raise ValueError("Delivery days must be at least 1")
        return v


class ProductResponse(BaseModel):
    productCode: str
    vendorCode: str
    productName: str
    category: str
    subcategory: str
    price: float
    hsnCode: str
    isTaxExempt: bool
    gstRate: float
    deliveryDays: int
    deliveryCost: float
    uom: str
    description: str | None
    marginPercentage: float | None
    directMarginAmount: float | None
    finalPrice: float
    status: str
    rejectionReason: str | None
    createdAt: datetime

    @classmethod
    def from_orm(cls, obj):
        return cls(
            productCode=obj.product_code,
            vendorCode=obj.vendor_code,
            productName=obj.product_name,
            category=obj.category,
            subcategory=obj.subcategory,
            price=float(obj.price),
            hsnCode=obj.hsn_code,
            isTaxExempt=obj.is_tax_exempt,
            gstRate=float(obj.gst_rate),
            deliveryDays=obj.delivery_days,
            deliveryCost=float(obj.delivery_cost),
            uom=obj.uom,
            description=obj.description,
            marginPercentage=float(obj.margin_percentage) if obj.margin_percentage is not None else None,
            directMarginAmount=float(obj.direct_margin_amount) if obj.direct_margin_amount is not None else None,
            finalPrice=float(obj.final_price),
            status=obj.status,
            rejectionReason=obj.rejection_reason,
            createdAt=obj.created_at,
        )

    model_config = {"from_attributes": True}


class ProductListItem(BaseModel):
    """Simplified response for GET /products list (matches spec)."""
    productCode: str
    productName: str
    vendor: str              # vendor name, not ID
    category: str
    subcategory: str
    price: float
    hsnCode: str
    isTaxExempt: bool
    gstRate: float
    uom: str
    deliveryDays: int
    costOfDelivery: float    # renamed from deliveryCost
    description: str | None
    status: str

    model_config = {"from_attributes": True}


class ApproveProductRequest(BaseModel):
    productIds: list[str]


class RejectProductRequest(BaseModel):
    reason: str


class PriceChangeRequestCreate(BaseModel):
    productCode: str
    vendorCode: str
    newPrice: float
    wefDate: date   # future date

    @field_validator("newPrice")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("New price must be greater than 0")
        return v


class PriceChangeRequestResponse(BaseModel):
    id: int
    productCode: str
    vendorCode: str
    newPrice: float
    wefDate: Any
    status: str
    rejectionReason: str | None
    createdAt: datetime
    reviewedAt: datetime | None
    reviewedBy: str | None

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            productCode=obj.product_code,
            vendorCode=obj.vendor_code,
            newPrice=float(obj.new_price),
            wefDate=obj.wef_date,
            status=obj.status,
            rejectionReason=obj.rejection_reason,
            createdAt=obj.created_at,
            reviewedAt=obj.reviewed_at,
            reviewedBy=obj.reviewed_by,
        )

    model_config = {"from_attributes": True}


class ApprovePriceChangeRequest(BaseModel):
    approvalId: int


class RejectPriceChangeRequest(BaseModel):
    reason: str


class MarginResponse(BaseModel):
    productCode: str
    productName: str
    vendorCode: str
    price: float
    marginPercentage: float | None
    directMarginAmount: float | None
    finalPrice: float

    @classmethod
    def from_orm(cls, obj):
        return cls(
            productCode=obj.product_code,
            productName=obj.product_name,
            vendorCode=obj.vendor_code,
            price=float(obj.price),
            marginPercentage=float(obj.margin_percentage) if obj.margin_percentage is not None else None,
            directMarginAmount=float(obj.direct_margin_amount) if obj.direct_margin_amount is not None else None,
            finalPrice=float(obj.final_price),
        )

    model_config = {"from_attributes": True}
