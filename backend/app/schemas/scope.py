from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import Meta


class ScopeItemWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    point_id: str
    included: bool
    priority: Literal["normal", "important"] = "normal"

class ScopeDraftWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=0)
    items: list[ScopeItemWrite]
class ScopeDraft(BaseModel):
    exam_id: str
    draft_version: int
    included_count: int
    important_count: int
    items: list[ScopeItemWrite]
    updated_at: datetime | None = None
class ScopeDraftResponse(BaseModel):
    data: ScopeDraft
    meta: Meta
class ScopeConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_draft_version: int = Field(ge=1)
class ScopeVersion(BaseModel):
    exam_id: str
    scope_version: int
    items: list[ScopeItemWrite]
    confirmed_at: datetime
class ScopeVersionResponse(BaseModel):
    data: ScopeVersion
    meta: Meta
