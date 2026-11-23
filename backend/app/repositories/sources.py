"""课程资料来源登记与读取。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Source


def create_source(session: Session, source: Source) -> Source:
    """只登记链接或笔记，尚未提取正文；事务由调用方管理。"""
    if not source.title.strip():
        raise ValueError("资料标题不能为空")
    if source.kind == "link":
        if not source.uri or not source.uri.strip() or source.note_text is not None:
            raise ValueError("链接资料需要地址，不能同时包含笔记正文")
    elif source.kind == "note":
        if not source.note_text or not source.note_text.strip() or source.uri is not None:
            raise ValueError("笔记资料需要正文，不能同时包含链接")
    else:
        raise ValueError("资料类型只能是 link 或 note")
    session.add(source)
    session.flush()
    return source


def list_sources(session: Session, course_id: str) -> list[Source]:
    return list(session.scalars(
        select(Source).where(Source.course_id == course_id)
        .order_by(Source.created_at, Source.id)
    ))
