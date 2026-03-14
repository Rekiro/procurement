from datetime import datetime

from pydantic import BaseModel, field_validator


# --- Create indent ---

class IndentItemCreate(BaseModel):
    productCode: str
    quantity: float
    size: str | None = None

    @field_validator("quantity")
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class IndentCreate(BaseModel):
    requestorEmail: str
    siteId: str
    forMonth: str              # "October 2025"
    isMonthly: bool
    category: str              # "Regular" or "Extra Material"
    items: list[IndentItemCreate]
    extraMaterialRequestId: str | None = None

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("Indent must have at least one item")
        return v

    @field_validator("category")
    @classmethod
    def valid_category(cls, v):
        if v not in ("Regular", "Extra Material"):
            raise ValueError("category must be 'Regular' or 'Extra Material'")
        return v


class IndentCreateResponse(BaseModel):
    message: str
    trackingNo: str
    status: str


# --- List indents ---

class IndentListItem(BaseModel):
    trackingNo: str
    monthYear: str
    requestDate: str           # "YYYY-MM-DD"
    siteName: str
    branchName: str | None
    category: str
    requestCategory: str | None
    siteBudget: float | None
    value: float
    balance: float | None
    status: str

    model_config = {"from_attributes": True}


# --- Indent detail ---

class IndentDetailProduct(BaseModel):
    srNo: int
    productGroup: str | None
    productName: str
    productDescription: str | None
    unit: str | None
    vendor: str | None
    quantity: float
    rate: float
    tax: float | None
    amount: float


class IndentDetailResponse(BaseModel):
    trackingNo: str
    requestDate: str
    monthYear: str
    branch: str | None
    branchGst: str | None
    client: str | None
    siteName: str
    requestCategory: str | None
    categoryType: str
    narration: str | None
    documentUrl: str | None
    vendor: str | None
    products: list[IndentDetailProduct]
    totalQty: float
    salesTotalBeforeTax: float
    salesTotalAfterTax: float
    purchaseTotalBeforeTax: float
    purchaseTotalAfterTax: float


# --- Update indent (PH edit modal) ---

class IndentUpdateItem(BaseModel):
    productCode: str
    quantity: float

    @field_validator("quantity")
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class IndentUpdate(BaseModel):
    branchGst: str
    requestCategory: str
    narration: str | None = None
    products: list[IndentUpdateItem]

    @field_validator("products")
    @classmethod
    def products_not_empty(cls, v):
        if not v:
            raise ValueError("Must have at least one product")
        return v


# --- Approve / Reject ---

class ApproveIndentRequest(BaseModel):
    indentIds: list[str]       # list of trackingNos


class RejectIndentRequest(BaseModel):
    trackingNo: str
    reason: str
