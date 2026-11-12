from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def request_id() -> str:
    return f"req_{uuid4().hex[:8]}"


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id(),
        }
    }
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """FastAPI 默认把参数错误报成 422，契约要求 400 VALIDATION_ERROR，这里统一转。"""
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(part) for part in first.get("loc", []) if part != "body")
    return error_response(
        status_code=400,
        code="VALIDATION_ERROR",
        message=first.get("msg", "请求参数不合法"),
        details={"field": field} if field else None,
    )
