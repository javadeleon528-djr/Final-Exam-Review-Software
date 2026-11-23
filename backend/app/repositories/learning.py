"""课程、知识目录和当前掌握档案的数据库操作。"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models import Course, KnowledgePoint, PointProfileEvent, UserPointProfile


LOCAL_USER_ID = "local_user"
MASTERY_STATUSES = frozenset({"not_started", "not_mastered", "basic", "mastered"})


def create_course(session: Session, course: Course) -> Course:
    session.add(course)
    session.flush()
    return course


def get_course(session: Session, course_id: str) -> Course | None:
    return session.get(Course, course_id)


def list_courses(session: Session) -> list[Course]:
    return list(session.scalars(select(Course).where(Course.archived_at.is_(None)).order_by(Course.created_at, Course.id)))


def create_point(
    session: Session, point: KnowledgePoint, *, user_id: str = LOCAL_USER_ID
) -> KnowledgePoint:
    """建目录节点；只有真正的知识点才建立初始自评档案。"""
    session.add(point)
    session.flush()
    if point.node_type == "point":
        session.add(UserPointProfile(user_id=user_id, point_id=point.id))
        session.flush()
    return point


def get_point(session: Session, point_id: str) -> KnowledgePoint | None:
    return session.get(KnowledgePoint, point_id)


def list_points(session: Session, course_id: str) -> list[KnowledgePoint]:
    return list(session.scalars(
        select(KnowledgePoint)
        .where(KnowledgePoint.course_id == course_id, KnowledgePoint.archived_at.is_(None))
        .order_by(KnowledgePoint.parent_id, KnowledgePoint.sort_order, KnowledgePoint.id)
    ))


def get_profile(
    session: Session, point_id: str, *, user_id: str = LOCAL_USER_ID
) -> UserPointProfile | None:
    return session.get(UserPointProfile, (user_id, point_id))


def update_self_status(
    session: Session,
    point_id: str,
    self_status: str,
    expected_version: int,
    *,
    user_id: str = LOCAL_USER_ID,
) -> UserPointProfile | None:
    """仅在版本相符时修改用户自评；返回 None 表示档案不存在或版本冲突。"""
    if self_status not in MASTERY_STATUSES:
        raise ValueError("无效的知识点掌握状态")
    previous = get_profile(session, point_id, user_id=user_id)
    if previous is None or previous.version != expected_version:
        return None
    old_value = previous.self_status
    result = session.execute(
        update(UserPointProfile)
        .where(
            UserPointProfile.user_id == user_id,
            UserPointProfile.point_id == point_id,
            UserPointProfile.version == expected_version,
        )
        .values(
            self_status=self_status,
            version=UserPointProfile.version + 1,
            self_updated_at=datetime.now(timezone.utc),
        )
    )
    if result.rowcount != 1:
        return None
    profile = get_profile(session, point_id, user_id=user_id)
    session.refresh(profile)
    session.add(PointProfileEvent(
        id=str(uuid4()), user_id=user_id, point_id=point_id,
        field_name="self_status", old_value=old_value,
        new_value=self_status, actor="user",
    ))
    session.flush()
    return profile
