from typing import Any

from pydantic import BaseModel


class Meta(BaseModel):
    request_id: str
    version: int | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str


class Error(BaseModel):
    error: ErrorBody
