from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.courses import router as courses_router
from app.api.errors import validation_exception_handler
from app.api.health import router as health_router

app = FastAPI(title="期末复习助手 API")

app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(health_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
