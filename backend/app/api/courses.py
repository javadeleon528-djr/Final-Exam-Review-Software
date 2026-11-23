from fastapi import APIRouter, Header

from app.api.errors import error_response, request_id
from app.schemas.course import CourseCreateRequest
from app.services import course_service
from app.services.course_service import DuplicateCourseName, InvalidCourseName

router = APIRouter()


@router.get("/courses")
def list_courses():
    courses = course_service.list_courses()
    return {
        "data": courses,
        "meta": {"request_id": request_id()},
    }


@router.post("/courses", status_code=201)
def create_course(
    payload: CourseCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    # Idempotency-Key 按契约必须传，但去重逻辑先不做，后面再补
    try:
        course = course_service.create_course(payload.name, payload.description)
    except InvalidCourseName:
        return error_response(
            status_code=400,
            code="VALIDATION_ERROR",
            message="课程名不能为空",
            details={"field": "name"},
        )
    except DuplicateCourseName as exc:
        return error_response(
            status_code=409,
            code="DUPLICATE_COURSE",
            message=f"已存在同名课程「{payload.name.strip()}」",
            details={
                "reason": "duplicate_name",
                "existing_course_id": exc.existing_course_id,
            },
        )

    return {
        "data": course,
        "meta": {"request_id": request_id()},
    }
