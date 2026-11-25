from sqlalchemy.orm import Session

from app.core.config import engine
from app.repositories import exams as exam_repo
from app.repositories.exams import ScopeDraftVersionConflict
from app.schemas.scope import ScopeDraft, ScopeDraftWriteRequest, ScopeItemWrite
from app.schemas.scope import ScopeDraft, ScopeDraftWriteRequest, ScopeItemWrite, ScopeVersion


class ExamNotFound(Exception):
    """考试不存在"""


class DraftConflict(Exception):
    """草稿版本冲突"""


class InvalidItems(Exception):
    """草稿条目本身不合法（重复、优先级错）"""


class InvalidPointIds(Exception):
    """知识点不存在、跨课程或已归档"""


def _items_to_schema(items) -> list[ScopeItemWrite]:
    return [
        ScopeItemWrite(
            point_id=i.point_id,
            included=i.included,
            priority="important" if i.priority == 1 else "normal",
        )
        for i in items
    ]


def _to_draft(exam_id, version, items, updated_at) -> ScopeDraft:
    schema_items = _items_to_schema(items)
    return ScopeDraft(
        exam_id=exam_id,
        draft_version=version,
        included_count=sum(1 for i in schema_items if i.included),
        important_count=sum(1 for i in schema_items if i.included and i.priority == "important"),
        items=schema_items,
        updated_at=updated_at,
    )


def get_draft(exam_id: str) -> ScopeDraft:
    with Session(engine) as session:
        if exam_repo.get_exam(session, exam_id) is None:
            raise ExamNotFound()
        draft, items = exam_repo.get_scope_draft(session, exam_id)
        if draft is None:
            return _to_draft(exam_id, 0, [], None)
        return _to_draft(exam_id, draft.draft_version, items, draft.updated_at)


def save_draft(exam_id: str, payload: ScopeDraftWriteRequest) -> ScopeDraft:
    tuples = [(i.point_id, i.included, i.priority) for i in payload.items]
    with Session(engine) as session:
        if exam_repo.get_exam(session, exam_id) is None:
            raise ExamNotFound()
        try:
            draft = exam_repo.save_scope_draft(
                session, exam_id, payload.expected_version, tuples
            )
        except ScopeDraftVersionConflict:
            session.rollback()
            raise DraftConflict()
        except ValueError as exc:
            session.rollback()
            message = str(exc)
            if any(k in message for k in ("不存在", "不属于", "只能选择", "已归档")):
                raise InvalidPointIds(message)
            raise InvalidItems(message)
        session.commit()
        _, saved = exam_repo.get_scope_draft(session, exam_id)
        return _to_draft(exam_id, draft.draft_version, saved, draft.updated_at)
class DraftNotConfirmed(Exception):
    """还没有正式版本"""


class EmptyScope(Exception):
    """空草稿不能确认"""


class CrossCoursePoint(Exception):
    """草稿含不属于本场考试的知识点"""


def _version_to_schema(version, items) -> ScopeVersion:
    return ScopeVersion(
        exam_id=version.exam_id,
        scope_version=version.version_no,
        items=_items_to_schema(items),
        confirmed_at=version.confirmed_at,
    )


def confirm(exam_id: str, expected_draft_version: int) -> ScopeVersion:
    with Session(engine) as session:
        if exam_repo.get_exam(session, exam_id) is None:
            raise ExamNotFound()
        try:
            version, items = exam_repo.confirm_scope(
                session, exam_id, expected_draft_version
            )
        except ScopeDraftVersionConflict:
            session.rollback()
            raise DraftConflict()
        except ValueError as exc:
            session.rollback()
            message = str(exc)
            if "至少" in message:
                raise EmptyScope(message)
            raise CrossCoursePoint(message)
        session.commit()
        return _version_to_schema(version, items)


def get_confirmed(exam_id: str, version_no: int | None = None) -> ScopeVersion:
    with Session(engine) as session:
        if exam_repo.get_exam(session, exam_id) is None:
            raise ExamNotFound()
        version, items = exam_repo.get_confirmed_scope(session, exam_id, version_no)
        if version is None:
            raise DraftNotConfirmed()
        return _version_to_schema(version, items)
