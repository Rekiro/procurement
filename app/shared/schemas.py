import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    errorType: str
    errorMessage: str
    location: str = ""

    model_config = {"extra": "allow"}


class ApiResponse(BaseModel):
    responseId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    results: Any = None


class ApiErrorResponse(BaseModel):
    responseId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    errors: list[ErrorDetail]


def success_response(results) -> dict:
    return {
        "responseId": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
