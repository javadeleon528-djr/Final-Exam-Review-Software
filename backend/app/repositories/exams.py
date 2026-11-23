"""考试信息与考试范围的数据库操作"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session

from app.db.models import (
    Exam,
    ScopeDraft,
    KnowledgePoint,
    ScopeDraftItem,
    ScopeItem,
    ScopeVersion,
    )

class ScopeDraftVersionConflict(Exception):
    """考试范围草稿版本冲突异常"""
    pass

def create_exam(session: Session, exam: Exam) -> Exam:
    """创建考试记录"""
    session.add(exam)  # 把对象放进session中的待处理缓存,标记要插入，不发sql
    session.flush()  # 把缓存里的变更，生成INSERT发给数据库，但是不提交事务 commit= flush() + 提交事务
    return exam

# creare_exam() 功能：创建一场考试

# select(Exam) ：构造SQL, select*from exam
# .where(Exam.course_id == course_id) : 只查这个课程的考试
# .order_by(Exam.exam_date, Exam.id): 排序，先按考试日期，再按考试ID
# session.scalars() ：发SQL给数据库，返回结果集
def get_exam(session: Session, exam_id: str) -> Exam | None:
    """根据考试ID获取考试记录"""
    return session.get(Exam, exam_id)  # session.get() 直接发sql查询数据库

def list_exams(session: Session , course_id: str) -> list[Exam]:
    """获取指定课程下的全部考试"""
    return list(
        session.scalars(
            select(Exam).where(Exam.course_id == course_id).order_by(Exam.exam_date, Exam.id)
        )
    )


# tuple是元组，有俩种情况 :None, []  或者 ScopeDraft, list[ScopeDraftItem]
# session.get(ScopeDraft, exam_id) : 根据主键查询单条记录 参数：模型类，主键值,查到返回ORM对象，查不到返回None ， 特点：优先去session一级缓存找，查不到返回None，只查一条记录，主键查询效率高
# select(Model) ：构造查询语句可以用链式: .where() .order_by() .limit() .offset()
# session.scalars() ：发SQL给数据库，返回结果集

def get_scope_draft(
    session: Session,
    exam_id: str
) -> tuple[ScopeDraft | None, list[ScopeDraftItem]]:
    """获取考试范围草稿及其全部知识点条目。"""

    # 第一步：根据考试ID获取草稿主体
    draft = session.get(ScopeDraft, exam_id)

    # 如果草稿不存在，返回 None 和空列表
    if draft is None:
        return None, []
   
    # 第二步：查询该草稿下的全部知识点条目
    items = list(
        session.scalars(
            select(ScopeDraftItem)
            .where(ScopeDraftItem.exam_id == exam_id)
            .order_by(
                ScopeDraftItem.priority,
                ScopeDraftItem.point_id
            )
        )
    )

    # 返回草稿主体和知识点条目
    return draft, items


def save_scope_draft(
    session: Session,
    exam_id: str,
    expected_version: int,
    items: list[tuple[str, bool, str]]
) -> ScopeDraft:
    """覆盖保存考试范围草稿，并更新版本号。"""

    # 1. 查询考试是否存在
    exam = session.get(Exam, exam_id)

    if exam is None:
        raise ValueError("考试不存在")

    # 2. 检查版本号是否合法
    if expected_version < 0:
        raise ValueError("版本号不能小于0")

    # 3. 检查传入的知识点是否重复、优先级是否合法
    point_ids = [point_id for point_id, _, _ in items]

    if len(point_ids) != len(set(point_ids)):
        raise ValueError("考试范围中存在重复知识点")

    if any(
        priority not in ("normal", "important") or not isinstance(included, bool)
        for _, included, priority in items
    ):
        raise ValueError("考试范围条目参数不合法")

    # 4. 检查所有知识点是否属于当前考试的课程
    if point_ids:
        points = list(
            session.scalars(
                select(KnowledgePoint)
                .where(KnowledgePoint.id.in_(point_ids))
            )
        )

        if len(points) != len(point_ids):
            raise ValueError("部分知识点不存在")

        for point in points:
            if point.course_id != exam.course_id:
                raise ValueError("知识点不属于当前考试的课程")

            if point.node_type != "point":
                raise ValueError("考试范围只能选择知识点")

            if point.archived_at is not None:
                raise ValueError("不能选择已归档的知识点")

    # 5. 获取当前草稿
    draft = session.get(ScopeDraft, exam_id)

    if draft is None:
        # 第一次保存：约定初始版本为0，保存后变为1
        if expected_version != 0:
            raise ScopeDraftVersionConflict("草稿版本冲突")

        draft = ScopeDraft(
            exam_id=exam_id,
            draft_version=1,
            updated_at=datetime.now(timezone.utc),
        )

        session.add(draft)
        session.flush()

    else:
        # 已有草稿：只有版本匹配时才能更新
        result = session.execute(
            update(ScopeDraft)
            .where(
                ScopeDraft.exam_id == exam_id,
                ScopeDraft.draft_version == expected_version
            )
            .values(
                draft_version=ScopeDraft.draft_version + 1,
                updated_at=datetime.now(timezone.utc),
            )
        )

        if result.rowcount != 1:
            raise ScopeDraftVersionConflict("草稿版本冲突")

        session.refresh(draft)

    # 6. 删除当前考试的旧草稿条目
    session.execute(
        delete(ScopeDraftItem)
        .where(ScopeDraftItem.exam_id == exam_id)
    )

    # 7. 写入新的草稿条目
    for point_id, included, priority in items:
        session.add(
            ScopeDraftItem(
                exam_id=exam_id,
                point_id=point_id,
                included=included,
                priority=1 if priority == "important" else 0
            )
        )

    # 8. 将变更发送给数据库，但不提交事务
    session.flush()

    return draft


def confirm_scope(
    session: Session, exam_id: str, expected_draft_version: int
) -> tuple[ScopeVersion, list[ScopeItem]]:
    """从当前草稿创建不可变的正式范围；调用方负责提交事务。"""
    exam = get_exam(session, exam_id)
    if exam is None:
        raise ValueError("考试不存在")
    draft, draft_items = get_scope_draft(session, exam_id)
    if draft is None or draft.draft_version != expected_draft_version:
        raise ScopeDraftVersionConflict("草稿版本冲突")
    if not draft_items or not any(item.included for item in draft_items):
        raise ValueError("至少选择一个考试知识点")
    points = {p.id: p for p in session.scalars(
        select(KnowledgePoint).where(KnowledgePoint.id.in_([i.point_id for i in draft_items]))
    )}
    if len(points) != len(draft_items) or any(
        points[item.point_id].course_id != exam.course_id for item in draft_items
    ):
        raise ValueError("草稿包含不属于本场考试的知识点")
    next_version = (session.scalar(
        select(func.max(ScopeVersion.version_no)).where(ScopeVersion.exam_id == exam_id)
    ) or 0) + 1
    version = ScopeVersion(id=str(uuid4()), exam_id=exam_id, version_no=next_version)
    session.add(version)
    session.flush()
    snapshots = [ScopeItem(
        scope_version_id=version.id,
        point_id=item.point_id,
        included=item.included,
        priority=item.priority,
        point_name_snapshot=points[item.point_id].name,
    ) for item in draft_items]
    session.add_all(snapshots)
    session.flush()
    return version, snapshots


def get_confirmed_scope(
    session: Session, exam_id: str, version_no: int | None = None
) -> tuple[ScopeVersion | None, list[ScopeItem]]:
    """读取最新或指定正式版本，历史条目保持原样。"""
    statement = select(ScopeVersion).where(ScopeVersion.exam_id == exam_id)
    if version_no is not None:
        statement = statement.where(ScopeVersion.version_no == version_no)
    else:
        statement = statement.order_by(ScopeVersion.version_no.desc())
    version = session.scalar(statement.limit(1))
    if version is None:
        return None, []
    items = list(session.scalars(
        select(ScopeItem).where(ScopeItem.scope_version_id == version.id)
        .order_by(ScopeItem.point_id)
    ))
    return version, items
