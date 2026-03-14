import uuid
from datetime import datetime

from pydantic import BaseModel


class ExtraMaterialRequestCreate(BaseModel):
    siteId: str
    monthYear: str   # "YYYY-MM"
    reason: str


class ExtraMaterialRequestResponse(BaseModel):
    id: uuid.UUID
    siteId: str
    requestorEmail: str
    monthYear: str
    reason: str
    status: str
    rejectionReason: str | None
    approvedBy: str | None
    reviewedAt: datetime | None
    createdAt: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        return cls(
            id=obj.id,
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


class ApproveEMRRequest(BaseModel):
    requestId: uuid.UUID


class RejectEMRRequest(BaseModel):
    rejectionReason: str
