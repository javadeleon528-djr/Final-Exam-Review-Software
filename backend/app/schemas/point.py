from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import Meta
from typing import Literal


class MasteryStatus(str, Enum):
    not_started = "not_started"
    not_mastered = "not_mastered"
    basic = "basic"
    mastered = "mastered"

class PointCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=160)
    node_type:Literal["chapter","point"]
    sort_order: int = Field(default=0, ge=0)
    parent_id: str | None = None
class Point(BaseModel):
    id: str
    course_id: str
    parent_id: str | None = None
    node_type:Literal["chapter","point"]
    sort_order: int = Field(default=0, ge=0)
    name: str
    self_status: MasteryStatus| None = None
    ai_status: MasteryStatus | None = None
    version: int | None = Field(ge=1)
class PointResponse(BaseModel):
    data: Point
    meta: Meta
class PointListData(BaseModel):
    course_id: str
    points: list[Point]
class PointListResponse(BaseModel):
    data: PointListData
    meta: Meta
class SelfStatusWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    self_status: MasteryStatus
    expected_version: int = Field(ge=1)
