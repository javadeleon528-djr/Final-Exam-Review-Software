from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Meta


class ExamCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    exam_date: date


class Exam(BaseModel):
    id: str
    course_id: str
    name: str
    exam_date: date


class ExamResponse(BaseModel):
    data: Exam
    meta: Meta


class ExamListResponse(BaseModel):
    data: list[Exam]
    meta: Meta
