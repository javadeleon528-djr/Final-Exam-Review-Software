from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import engine
from app.db.models import Course as CourseModel
from app.schemas.course import Course


class InvalidCourseName(Exception):
    """课程名去掉首尾空格后为空"""
class DuplicateCourseName(Exception):
    """同名课程已存在"""

    def __init__(self, existing_course_id: str) -> None:
        self.existing_course_id = existing_course_id

def _to_schema(row: CourseModel) -> Course:
    return Course(
        id=row.id,
        name=row.name,
        description=row.description,
        created_at=row.created_at,
        archived_at=row.archived_at,
    )
def list_courses() -> list[Course]:
    with Session(engine) as session:
        rows = session.scalars(
            select(CourseModel).order_by(CourseModel.created_at)
        ).all()
        return [_to_schema(row) for row in rows]
def create_course(name: str, description: str | None = None) -> Course:
    cleaned = name.strip()
    if not cleaned:
        raise InvalidCourseName()

    with Session(engine) as session:
        existing = session.scalars(
            select(CourseModel).where(CourseModel.name == cleaned).limit(1)
        ).first()
        if existing is not None:
            raise DuplicateCourseName(existing.id)

        row = CourseModel(
            id=f"course_{uuid4().hex}",
            name=cleaned,
            description=description,
            created_at=datetime.now(timezone.utc),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return _to_schema(row)
