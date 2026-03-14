import uuid
from datetime import datetime

from pydantic import BaseModel


class SiteOption(BaseModel):
    siteId: str
    siteName: str
    city: str
    state: str

    model_config = {"from_attributes": True}


# Simplified response for GET /user-sites (spec format)
class UserSiteItem(BaseModel):
    siteId: str
    siteName: str

    model_config = {"from_attributes": True}


# --- Material Catalog response (matches spec exactly) ---

class SiteDetails(BaseModel):
    siteId: str
    siteName: str
    budget: float | None
    balance: float | None


class FilterOption(BaseModel):
    value: str
    label: str


class CatalogFilterOptions(BaseModel):
    categories: list[FilterOption]
    brands: list[FilterOption]


class CatalogProduct(BaseModel):
    periodFrom: str | None
    vendorName: str
    productCode: str
    productName: str
    landedPrice: float
    manufacturedBy: str | None
    brandName: str | None
    hsnCode: str
    packaging: str          # maps to uom
    usedFor: str | None
    category: str
    lifeCycleDays: int | None
    costOfTransportationPerKM: float | None
    orderLeadTimeDays: int
    deliveryBy: str | None
    netProductCostPerDay: float | None
    gstSetOffAvailable: bool
    financeTreatment: str | None


class MaterialCatalogResponse(BaseModel):
    siteDetails: SiteDetails
    filterOptions: CatalogFilterOptions
    products: list[CatalogProduct]


# --- History endpoints ---

class SiteOrderHistoryItem(BaseModel):
    """Spec #8.6: Site Order History — indent-based."""
    siteId: str
    trackingNo: str
    requestDate: str            # "YYYY-MM-DD"
    siteBudget: float | None
    value: float
    status: str
    balance: float | None

    model_config = {"from_attributes": True}


class SitePoHistoryItem(BaseModel):
    poNumber: str
    siteId: str
    poDate: datetime
    status: str
    totalValue: float
    expectedDeliveryDate: datetime | None
    dateOfDelivery: datetime | None

    model_config = {"from_attributes": True}


class SiteIndentHistoryItem(BaseModel):
    id: uuid.UUID
    trackingNo: str
    requestorEmail: str
    forMonth: str
    category: str
    status: str
    totalValue: float
    createdAt: datetime

    model_config = {"from_attributes": True}
