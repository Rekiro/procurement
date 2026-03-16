import uuid
from datetime import date, datetime

from pydantic import BaseModel, field_validator


# --- PO Creation (used internally by indent approval) ---

class PoItemCreate(BaseModel):
    indentItemId: uuid.UUID | None = None
    productId: uuid.UUID | None = None
    productName: str
    quantity: float
    landedPrice: float

    @field_validator("quantity", "landedPrice")
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Must be greater than 0")
        return v


class PoCreate(BaseModel):
    indentId: uuid.UUID
    vendorId: uuid.UUID
    expectedDeliveryDate: date | None = None
    items: list[PoItemCreate]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("PO must have at least one item")
        return v


# --- PO Update (parsed from multipart 'data' JSON string) ---

class PoUpdateData(BaseModel):
    deliveryType: str | None = None       # "Hand" or "Courier"
    courierName: str | None = None
    podNumber: str | None = None
    status: str | None = None              # "In Transit", "Delivered", "Not Delivered"
    dateOfDelivery: datetime | None = None  # ISO datetime string
    reason: str | None = None


# --- GRN (parsed from multipart 'data' JSON string) ---

class GrnItemData(BaseModel):
    itemId: str
    receivedQuantity: float
    isAccepted: bool


class GrnData(BaseModel):
    items: list[GrnItemData]
    predefinedComment: str | None = None
    comments: str | None = None
    requestorEmail: str = "admin@smart.com"


# --- PO List Item (spec #9.1 / #10.1) ---

class PoListItem(BaseModel):
    """Rich PO list item matching the spec for both vendor and PH views."""
    materialRequestId: str | None       # indent tracking_no
    siteName: str | None
    region: str | None
    dcNumber: str | None
    poNumber: str
    dcDate: str | None                  # "YYYY-MM-DD"
    poDate: str                         # "YYYY-MM-DD"
    deliveryType: str | None
    tat: int | None
    expectedDeliveryDate: str | None    # "YYYY-MM-DD"
    status: str
    courierName: str | None
    podNumber: str | None
    dateOfDelivery: str | None          # "YYYY-MM-DD"
    podImageUrl: str | None
    signedPodUrl: str | None
    signedDcUrl: str | None
    signedDcISmartUrl: str | None
    tatStatus: str | None
    reason: str | None


# --- Responses ---

class PoItemResponse(BaseModel):
    id: uuid.UUID
    itemId: str
    productCode: str | None
    productName: str
    quantity: float
    landedPrice: float
    totalAmount: float

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            itemId=obj.item_id,
            productCode=obj.product_code,
            productName=obj.product_name,
            quantity=float(obj.quantity),
            landedPrice=float(obj.landed_price),
            totalAmount=float(obj.total_amount),
        )


class PoResponse(BaseModel):
    id: uuid.UUID
    poNumber: str
    indentId: uuid.UUID | None
    vendorCode: str | None
    vendorName: str | None
    siteId: str
    poDate: datetime
    expectedDeliveryDate: datetime | None
    tat: int | None
    deliveryType: str | None
    courierName: str | None
    podNumber: str | None
    status: str
    dateOfDelivery: datetime | None
    totalValue: float
    createdAt: datetime
    items: list[PoItemResponse] = []

    @classmethod
    def from_orm(cls, obj, items=None, vendor_name=None):
        return cls(
            id=obj.id,
            poNumber=obj.po_number,
            indentId=obj.indent_id,
            vendorCode=obj.vendor_code,
            vendorName=vendor_name,
            siteId=obj.site_id,
            poDate=obj.po_date,
            expectedDeliveryDate=obj.expected_delivery_date,
            tat=obj.tat,
            deliveryType=obj.delivery_type,
            courierName=obj.courier_name,
            podNumber=obj.pod_number,
            status=obj.status,
            dateOfDelivery=obj.date_of_delivery,
            totalValue=float(obj.total_value),
            createdAt=obj.created_at,
            items=[PoItemResponse.from_orm(i) for i in (items or [])],
        )


class GrnItemResponse(BaseModel):
    id: uuid.UUID
    itemId: str
    itemName: str
    orderedQuantity: float
    receivedQuantity: float
    isAccepted: bool
    deliveryStatus: str   # "Complete", "Partial", "Over-Delivered"

    @classmethod
    def from_orm(cls, obj):
        ordered = float(obj.ordered_quantity)
        received = float(obj.received_quantity)
        if received >= ordered:
            ds = "Over-Delivered" if received > ordered else "Complete"
        else:
            ds = "Partial"
        return cls(
            id=obj.id,
            itemId=obj.item_id,
            itemName=obj.item_name,
            orderedQuantity=ordered,
            receivedQuantity=received,
            isAccepted=obj.is_accepted,
            deliveryStatus=ds,
        )


class GrnResponse(BaseModel):
    id: uuid.UUID
    poId: uuid.UUID
    poNumber: str
    requestorEmail: str
    predefinedComment: str | None
    comments: str | None
    signedDcUrl: str
    photoUrls: list[str] = []
    submittedAt: datetime
    items: list[GrnItemResponse] = []

    @classmethod
    def from_orm(cls, obj, items=None, photos=None):
        return cls(
            id=obj.id,
            poId=obj.po_id,
            poNumber=obj.po_number,
            requestorEmail=obj.requestor_email,
            predefinedComment=obj.predefined_comment,
            comments=obj.comments,
            signedDcUrl=obj.signed_dc_url,
            photoUrls=[p.photo_url for p in (photos or [])],
            submittedAt=obj.submitted_at,
            items=[GrnItemResponse.from_orm(i) for i in (items or [])],
        )
