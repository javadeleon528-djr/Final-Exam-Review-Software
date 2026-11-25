from uuid import uuid4
from sqlalchemy.orm import Session

from app.core.config import engine
from app.db.models import KnowledgePoint
from app.repositories import learning
from app.schemas.point import Point, PointListData


class CourseNotFound(Exception):
    """课程不存在"""


class PointNotFound(Exception):
    """知识点不存在"""


class InvalidParent(Exception):
    """父节点不合法"""


class InvalidName(Exception):
    """名称是纯空格"""


class VersionConflict(Exception):
    """版本号不匹配"""

    def __init__(self, current_version: int) -> None:
        self.current_version = current_version


def _to_schema(row: KnowledgePoint, profile=None) -> Point:
    return Point(
        id=row.id,
        course_id=row.course_id,
        parent_id=row.parent_id,
        name=row.name,
        node_type=row.node_type,
        sort_order=row.sort_order,
        self_status=profile.self_status if profile else None,
        ai_status=profile.ai_status if profile else None,
        version=profile.version if profile else None,
    )


def list_points(course_id: str) -> PointListData:
    with Session(engine) as session:
        if learning.get_course(session, course_id) is None:
            raise CourseNotFound()
        points = []
        for row in learning.list_points(session, course_id):
            profile = learning.get_profile(session, row.id) if row.node_type == "point" else None
            points.append(_to_schema(row, profile))
        return PointListData(course_id=course_id, points=points)


def create_point(course_id, name, node_type, parent_id=None, sort_order=0) -> Point:
    cleaned = name.strip()
    if not cleaned:
        raise InvalidName()
    with Session(engine) as session:
        if learning.get_course(session, course_id) is None:
            raise CourseNotFound()
        if parent_id is not None:
            parent = learning.get_point(session, parent_id)
            if (parent is None or parent.course_id != course_id
                    or parent.archived_at is not None or parent.node_type != "chapter"):
                raise InvalidParent()
        row = KnowledgePoint(
            id=f"point_{uuid4().hex}",
            course_id=course_id,
            parent_id=parent_id,
            node_type=node_type,
            name=cleaned,
            sort_order=sort_order,
        )
        learning.create_point(session, row)   
        session.commit()                     
        profile = learning.get_profile(session, row.id) if node_type == "point" else None
        return _to_schema(row, profile)


def update_self_status(point_id, self_status, expected_version) -> Point:
    with Session(engine) as session:
        row = learning.get_point(session, point_id)
        if row is None:
            raise PointNotFound()
        profile = learning.get_profile(session, point_id)
        if profile is None:                    # 章节节点没有档案
            raise PointNotFound()
        try:
            updated = learning.update_self_status(
                session, point_id, self_status, expected_version
            )
        except ValueError:
            raise InvalidName()
        if updated is None:                    # 版本对不上
            raise VersionConflict(profile.version)
        session.commit()
        return _to_schema(row, updated)
