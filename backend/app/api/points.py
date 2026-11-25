from fastapi import APIRouter , Header
from app.api.errors import error_response , request_id
from app.schemas.point import PointCreateRequest , SelfStatusWriteRequest
from app.services import point_service

router = APIRouter()

@router.get("/courses/{course_id}/points")
def list_points(course_id : str):
    try:
        data  = point_service.list_points(course_id)
    except point_service.CourseNotFound:
        return error_response(404 , "NOT_FOUND" , "课程不存在"  , {"course_id": course_id} )
    return {"data": data, "meta": {"request_id": request_id()}}
@router.post("/courses/{course_id}/points", status_code=201)
def create_point(
    course_id: str,
    payload: PointCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    try:
        point = point_service.create_point(
            course_id, payload.name, payload.node_type, payload.parent_id, payload.sort_order
        )
    except point_service.CourseNotFound:
        return error_response(404, "NOT_FOUND", "课程不存在", {"course_id": course_id})
    except point_service.InvalidName:
        return error_response(400, "VALIDATION_ERROR", "名称不能为空", {"field": "name"})
    except point_service.InvalidParent:
        return error_response(400, "VALIDATION_ERROR", "父节点不合法", {"field": "parent_id"})
    return {"data": point, "meta": {"request_id": request_id()}}


@router.put("/points/{point_id}/self-status")
def update_self_status(
    point_id: str,
    payload: SelfStatusWriteRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    try:
        point = point_service.update_self_status(
            point_id, payload.self_status.value, payload.expected_version
        )
    except point_service.PointNotFound:
        return error_response(404, "NOT_FOUND", "知识点不存在", {"point_id": point_id})
    except point_service.VersionConflict as exc:
        return error_response(409, "VERSION_CONFLICT", "版本冲突，请刷新后重试", {
            "current_version": exc.current_version,
            "your_version": payload.expected_version,
        })
    return {"data": point, "meta": {"request_id": request_id()}}