from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# --- Create (EP34) ---

class ExtraMaterialRequestCreate(BaseModel):
    siteId: str = Field(..., min_length=1)
    monthYear: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    requestorEmail: EmailStr = "admin@smart.com"


# --- Approve / Reject ---

class ApproveEMRRequest(BaseModel):
    emrIds: list[str]   # business IDs like ["EMR-2026-001"]


class RejectEMRRequest(BaseModel):
    reason: str


# --- List item response (EP35) ---

class EMRListItem(BaseModel):
    emrId: str
    siteName: str
    monthYear: str          # "November 2025"
    reason: str
    requesterName: str
    requestDate: str        # ISO datetime
    status: str


# --- Create / detail response ---

class ExtraMaterialRequestResponse(BaseModel):
    emrId: str
    siteId: str
    requestorEmail: str
    monthYear: str          # "YYYY-MM"
    reason: str
    status: str
    rejectionReason: str | None
    approvedBy: str | None
    reviewedAt: datetime | None
    createdAt: datetime

    @classmethod
    def from_orm(cls, obj):
        return cls(
            emrId=obj.emr_id,
            siteId=obj.site_id,
            requestorEmail=obj.requestor_email,
            monthYear=obj.month_year.strftime("%Y-%m") if obj.month_year else "",
            reason=obj.reason,
            status=obj.status,
            rejectionReason=obj.rejection_reason,
            approvedBy=obj.approved_by,
            reviewedAt=obj.reviewed_at,
            createdAt=obj.created_at,
        )
