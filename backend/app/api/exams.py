from fastapi import APIRouter , Header
from app.api.errors import error_response, request_id
from app.schemas.exam import ExamCreateRequest
from app.services import exam_service

router = APIRouter()

@router.get("/courses/{course_id}/exams")
def list_exams(course_id:str):
    try:
        data = exam_service.list_exams(course_id)
    except exam_service.CourseNotFound:
        return error_response(404 , "NOT_FOUND" , "课程不存在"  ,{"course_id": course_id} )
    return {"data": data, "meta": {"request_id": request_id()}}
@router.post("/courses/{course_id}/exams", status_code=201)
def create_exam(
    course_id: str,
    payload: ExamCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    try:
        exam = exam_service.create_exam(course_id, payload.name, payload.exam_date)
    except exam_service.CourseNotFound:
        return error_response(404, "NOT_FOUND", "课程不存在", {"course_id": course_id})
    except exam_service.InvalidExamName:
        return error_response(400, "VALIDATION_ERROR", "考试名不能为空", {"field": "name"})
    return {"data": exam, "meta": {"request_id": request_id()}}