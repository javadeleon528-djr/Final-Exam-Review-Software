from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.api.scopes import router as scopes_router
from app.api.courses import router as courses_router
from app.api.errors import validation_exception_handler
from app.api.health import router as health_router
from app.api.points import router as points_router
from app.api.exams import router as exams_router

app = FastAPI(title="期末复习助手 API")

app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(health_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
app.include_router(points_router, prefix="/api/v1")
app.include_router(exams_router, prefix="/api/v1")
app.include_router(scopes_router, prefix="/api/v1")
