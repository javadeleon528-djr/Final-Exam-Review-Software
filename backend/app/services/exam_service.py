from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import engine
from app.db.models import Exam as ExamModel
from app.repositories import exams as exam_repo
from app.repositories import learning
from app.schemas.exam import Exam


class CourseNotFound(Exception):
    """课程不存在"""


class InvalidExamName(Exception):
    """考试名是纯空格"""


def _to_schema(row: ExamModel) -> Exam:
    return Exam(
        id=row.id,
        course_id=row.course_id,
        name=row.name,
        exam_date=row.exam_date,
    )
def list_exams(course_id: str) -> list[Exam]:
    with Session(engine) as session:
        if learning.get_course(session, course_id) is None:
            raise CourseNotFound()
        return [_to_schema(row) for row in exam_repo.list_exams(session, course_id)]
def create_exam(course_id: str, name: str, exam_date) -> Exam:
    cleaned = name.strip()
    if not cleaned:
        raise InvalidExamName()
    with Session(engine) as session:
        if learning.get_course(session, course_id) is None:
            raise CourseNotFound()
        row = ExamModel(
            id=f"exam_{uuid4().hex}",
            course_id=course_id,
            name=cleaned,
            exam_date=exam_date,
        )
        exam_repo.create_exam(session, row)   
        session.commit()                      
        return _to_schema(row)