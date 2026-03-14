import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    isRead: bool
    link: str | None
    createdAt: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        return cls(
            id=obj.id,
            title=obj.title,
            message=obj.message,
            isRead=obj.is_read,
            link=obj.link,
            createdAt=obj.created_at,
        )


class MarkAsReadRequest(BaseModel):
    ids: list[uuid.UUID]
