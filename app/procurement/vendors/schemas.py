from typing import Any

from pydantic import BaseModel, EmailStr, field_validator

VALID_STATES = ["Maharashtra", "Karnataka", "Tamil Nadu", "Delhi", "Uttar Pradesh", "Gujarat", "Rajasthan"]
VALID_NATURE_OF_BUSINESS = ["Manufacturing", "Distribution", "Services", "Retail", "Wholesale"]


class VendorCreate(BaseModel):
    vendorName: str
    emailId: str
    state: str
    natureOfBusiness: str

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        if v not in VALID_STATES:
            raise ValueError(f"state must be one of {VALID_STATES}")
        return v

    @field_validator("natureOfBusiness")
    @classmethod
    def validate_nature_of_business(cls, v):
        if v not in VALID_NATURE_OF_BUSINESS:
            raise ValueError(f"natureOfBusiness must be one of {VALID_NATURE_OF_BUSINESS}")
        return v


class VendorResponse(BaseModel):
    vendorCode: str
    vendorName: str
    emailId: str
    state: str
    natureOfBusiness: str
    status: str

    @classmethod
    def from_orm(cls, obj):
        return cls(
            vendorCode=obj.vendor_code,
            vendorName=obj.company_name,
            emailId=obj.email,
            state=obj.state,
            natureOfBusiness=obj.nature_of_business,
            status=obj.status,
        )

    model_config = {"from_attributes": True}


class GstDetailData(BaseModel):
    state: str
    gstNumber: str
    gstCertificate: str  # field name of the uploaded file in the form


class VendorApplicationData(BaseModel):
    """Text-only part of the multipart vendor application (parsed from 'data' JSON field)."""
    name: str
    nameOfOwner: str
    email: EmailStr
    designation: str
    category: str
    typesOfBusiness: str
    addressLine1: str
    addressLine2: str | None = None
    state: str
    district: str
    city: str
    pinCode: str
    gstDetails: list[GstDetailData]

    @field_validator("name", "nameOfOwner", "designation")
    @classmethod
    def min_2_chars(cls, v, info):
        if len(v.strip()) < 2:
            raise ValueError(f"{info.field_name} must be at least 2 characters")
        return v

    @field_validator("addressLine1")
    @classmethod
    def address_min_5(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("addressLine1 must be at least 5 characters")
        return v

    @field_validator("pinCode")
    @classmethod
    def pin_6_digits(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError("pinCode must be exactly 6 digits")
        return v

    @field_validator("gstDetails")
    @classmethod
    def gst_non_empty(cls, v):
        if not v:
            raise ValueError("gstDetails must contain at least one GST entry")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        if v not in VALID_STATES:
            raise ValueError(f"state must be one of {VALID_STATES}")
        return v


class VendorApplicationListItem(BaseModel):
    vendorCode: str
    name: str
    category: str
    nameOfOwner: str
    email: str
    status: str

    @classmethod
    def from_orm(cls, obj):
        return cls(
            vendorCode=obj.vendor_code,
            name=obj.name,
            category=obj.category,
            nameOfOwner=obj.name_of_owner,
            email=obj.email,
            status=obj.status,
        )

    model_config = {"from_attributes": True}


class VendorApplicationResponse(BaseModel):
    vendorCode: str
    name: str
    nameOfOwner: str
    email: str
    designation: str
    category: str
    typesOfBusiness: str
    shopAndEstablishmentNoUrl: str | None
    panNoUrl: str | None
    addressLine1: str
    addressLine2: str | None
    state: str
    district: str
    city: str
    pinCode: str
    gstDetails: Any
    aadhaarOrUdyamCopyUrl: str | None
    msmeCertificateUrl: str | None
    boardResolutionUrl: str | None
    cancelledChequeUrl: str | None
    escalationMatrixUrl: str | None
    branchOfficeDetailsUrl: str | None
    status: str

    @classmethod
    def from_orm(cls, obj):
        return cls(
            vendorCode=obj.vendor_code,
            name=obj.name,
            nameOfOwner=obj.name_of_owner,
            email=obj.email,
            designation=obj.designation,
            category=obj.category,
            typesOfBusiness=obj.types_of_business,
            shopAndEstablishmentNoUrl=obj.shop_establishment_url,
            panNoUrl=obj.pan_url,
            addressLine1=obj.address_line1,
            addressLine2=obj.address_line2,
            state=obj.state,
            district=obj.district,
            city=obj.city,
            pinCode=obj.pin_code,
            gstDetails=obj.gst_details,
            aadhaarOrUdyamCopyUrl=obj.aadhaar_udyam_url,
            msmeCertificateUrl=obj.msme_certificate_url,
            boardResolutionUrl=obj.board_resolution_url,
            cancelledChequeUrl=obj.cancelled_cheque_url,
            escalationMatrixUrl=obj.escalation_matrix_url,
            branchOfficeDetailsUrl=obj.branch_office_details_url,
            status=obj.status,
        )

    model_config = {"from_attributes": True}


class ApproveApplicationRequest(BaseModel):
    vendorIds: list[str]  # list of vendor_codes like ["VEN0001", "VEN0002"]


class RejectApplicationRequest(BaseModel):
    reason: str
