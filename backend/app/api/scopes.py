from fastapi import APIRouter, Header

from app.api.errors import error_response, request_id
from app.schemas.scope import ScopeDraftWriteRequest
from app.services import scope_service
from fastapi import APIRouter, Header, Query
from app.schemas.scope import ScopeConfirmRequest, ScopeDraftWriteRequest
router = APIRouter()


@router.get("/exams/{exam_id}/scope-draft")
def get_scope_draft(exam_id: str):
    try:
        data = scope_service.get_draft(exam_id)
    except scope_service.ExamNotFound:
        return error_response(404, "NOT_FOUND", "考试不存在", {"exam_id": exam_id})
    return {"data": data, "meta": {"request_id": request_id()}}


@router.put("/exams/{exam_id}/scope-draft")
def save_scope_draft(
    exam_id: str,
    payload: ScopeDraftWriteRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    try:
        data = scope_service.save_draft(exam_id, payload)
    except scope_service.ExamNotFound:
        return error_response(404, "NOT_FOUND", "考试不存在", {"exam_id": exam_id})
    except scope_service.DraftConflict as exc:
        return error_response(409, "VERSION_CONFLICT", "草稿已有更新，请查看差异后重试",
                              {"your_version": payload.expected_version})
    except scope_service.InvalidPointIds as exc:
        return error_response(422, "VALIDATION_ERROR", str(exc), {"reason": str(exc)})
    except scope_service.InvalidItems as exc:
        return error_response(400, "VALIDATION_ERROR", str(exc), {"reason": str(exc)})
    return {"data": data, "meta": {"request_id": request_id()}}
@router.post("/exams/{exam_id}/scope-confirmations", status_code=201)
def confirm_scope(
    exam_id: str,
    payload: ScopeConfirmRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    try:
        data = scope_service.confirm(exam_id, payload.expected_draft_version)
    except scope_service.ExamNotFound:
        return error_response(404, "NOT_FOUND", "考试不存在", {"exam_id": exam_id})
    except scope_service.DraftConflict:
        return error_response(409, "VERSION_CONFLICT", "草稿已有更新，请查看差异后重试",
                              {"your_version": payload.expected_draft_version})
    except scope_service.EmptyScope as exc:
        return error_response(422, "PLAN_INVALID", str(exc), {"reason": str(exc)})
    except scope_service.CrossCoursePoint as exc:
        return error_response(422, "PLAN_INVALID", str(exc), {"reason": str(exc)})
    return {"data": data, "meta": {"request_id": request_id()}}


@router.get("/exams/{exam_id}/scope")
def get_confirmed_scope(exam_id: str, version: int | None = Query(default=None, ge=1)):
    try:
        data = scope_service.get_confirmed(exam_id, version)
    except scope_service.ExamNotFound:
        return error_response(404, "NOT_FOUND", "考试不存在", {"exam_id": exam_id})
    except scope_service.DraftNotConfirmed:
        return error_response(404, "NOT_FOUND", "还没有已确认的范围", {"exam_id": exam_id})
    return {"data": data, "meta": {"request_id": request_id()}}
