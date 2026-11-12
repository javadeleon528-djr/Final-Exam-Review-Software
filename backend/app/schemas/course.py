from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Meta


class CourseCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class Course(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_at: datetime
    archived_at: datetime | None = None


class CourseListResponse(BaseModel):
    data: list[Course]
    meta: Meta
