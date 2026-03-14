import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ApiLogEntry(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    method: str
    path: str
    status_code: int
    user_email: str | None
    user_role: str | None
    duration_ms: int
    client_ip: str | None

    model_config = {"from_attributes": True}
