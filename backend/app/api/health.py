from uuid import uuid4
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.db.check import check_database

router = APIRouter()

@router.get("/health")
def health():
    try:
        check_database()
    except  Exception:
        return JSONResponse(
            status_code=503,
            content={
                "error":{
                    "code": "STORAGE_ERROR",
                    "message": "数据库暂时无法连接，请稍后重试",
                    "details": {"database": "unavailable"},
                    "request_id": f"req_{uuid4().hex[:8]}",
                }
            }
        )
    return{
        "data":{"status": "ok", "database": "ok"},
        "meta":{"request_id": f"req_{uuid4().hex[:8]}"},
    }