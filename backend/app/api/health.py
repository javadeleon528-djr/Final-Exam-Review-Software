from uuid import uuid4
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.config import engine
from app.db.connection import check_database
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

router = APIRouter()
def _database_ready() ->bool:
    if not check_database(engine):
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM courses LIMIT 1"))
        return True
    except SQLAlchemyError:
        return False
@router.get("/health")
def health():
    if not _database_ready():
        return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "STORAGE_ERROR",
                        "message": "数据库暂时无法连接，请稍后重试",
                        "details": {"database": "unavailable"},
                        "request_id": f"req_{uuid4().hex[:8]}",
                    }
                },
            )
    return {
            "data": {"status": "ok", "database": "ok"},
            "meta": {"request_id": f"req_{uuid4().hex[:8]}"},
        }