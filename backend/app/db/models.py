from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint, Boolean
from datetime import date, datetime, timezone

# 基础父类，所有表都继承它。
class Base(DeclarativeBase):
    pass

# Course 模型与课程接口的字段保持一致。
class Course(Base):
    __tablename__ = "courses"

    # id 是稳定的字符串标识，由创建课程的业务逻辑生成。
    id: Mapped[str] = mapped_column(String(64), primary_key=True, comment="课程唯一业务ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="课程名称")
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="课程描述")
    created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda:datetime.now(timezone.utc),  # default是mapped_column的函数，如果代码没有手动输入给这个字段复制，那么默认用这个值
    comment="创建时间（utc时区）"
    )
    archived_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
    comment="归档时间，非空代表已归档"
    )

class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    # ID:知识点唯一标识

    id:Mapped[str] = mapped_column(String(64), primary_key=True, comment="知识点业务ID")
    course_id:Mapped[str] = mapped_column(String(64), nullable=False, comment="所属课程ID")
    # 父节点ID,自引用，根节点为null
    parent_id:Mapped[str | None] = mapped_column(String(64), nullable=True, comment="父节点ID,根节点为空")
    # 节点类型，例如:chapter / sectiomn / point
    node_type:Mapped[str] = mapped_column(String(20) , nullable=False , comment="节点类型")
    # 节点名称
    name:Mapped[str] = mapped_column(String(160), nullable=False, comment="知识点名称")
    # 牌序字段，同层级内排序
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False,default=0, comment="同层级内排序")

    # 三个时间段
    created_at:Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda:datetime.now(timezone.utc),
    comment="创建时间UTC"
    )
    # Mapped[T] 其实就是解释性的语言，说是什么变量的，mapped_column才是真的数据库构建
    updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda:datetime.now(timezone.utc),
    onupdate=lambda:datetime.now(timezone.utc),
    comment="更新时间UTC"
    )
    archived_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
    comment="归档时间，非空代表已归档"
    )

    # 核心约束：组合外键，保证【父节点必须属于同一个课程】
    # 给整张表加表级约束
    __table_args__ = (
    # 普通外键
    ForeignKeyConstraint(
    ["course_id"],
    ["courses.id"],
    name="fk_kp_course_id",
    ondelete="RESTRICT"
    ),
    UniqueConstraint("course_id", "id", name="uq_kp_course_id_id"),
    # 左边：当前表俩列(course_id , parent_id) 右边：引用自表knowledge_points的俩列(course_id , id)
    ForeignKeyConstraint(
    ["course_id" , "parent_id"],
    ["knowledge_points.course_id" , "knowledge_points.id"],
    name="fk_kp_parent_same_course",
    ondelete="RESTRICT"
    ),
    CheckConstraint("node_type IN ('chapter', 'point')", name="ck_kp_node_type"),
    CheckConstraint("sort_order >= 0", name="ck_kp_sort_order"),
    CheckConstraint("parent_id IS NULL OR parent_id <> id", name="ck_kp_parent_not_self"),
    Index("ix_kp_course_parent_sort", "course_id", "parent_id", "sort_order"),
    )
# 自引用关系（方便ORM查询树形）
# 告诉SQLAlchemy:这组父子关联，是靠course_id + parent_id 这俩个字段作为外键
# remote_side=[id]:区分远端（父那一侧的主键是id）
# back_populates :双向绑定
# kp.parent -> 拿到父节点对象
# kp.children -> 拿到所有子节点对象
    parent: Mapped["KnowledgePoint | None"] = relationship(
        "KnowledgePoint",
        remote_side=[id],
        foreign_keys=[course_id, parent_id],
        back_populates="children"
    )
    children: Mapped[list["KnowledgePoint"]] = relationship(
        "KnowledgePoint",
        foreign_keys=[course_id, parent_id],
        back_populates="parent"
    )


class UserPointProfile(Base):
    """一位用户对一个知识点的当前掌握状态；自评和 AI 建议独立保存。"""

    __tablename__ = "user_point_profiles"
    __table_args__ = (
        CheckConstraint(
            "self_status IN ('not_started', 'not_mastered', 'basic', 'mastered')",
            name="ck_profile_self_status",
        ),
        CheckConstraint(
            "ai_status IS NULL OR ai_status IN ('not_started', 'not_mastered', 'basic', 'mastered')",
            name="ck_profile_ai_status",
        ),
        CheckConstraint("version >= 1", name="ck_profile_version"),
    )

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    point_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("knowledge_points.id", ondelete="RESTRICT"), primary_key=True
    )
    self_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")
    ai_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    self_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    ai_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Exam(Base):
    """考试课程信息"""

    __tablename__ = "exams"

    id:Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="考试唯一业务ID"
    )

    course_id:Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="所属课程ID"
    )

    name:Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="考试名称"
    )
    # date类型：python日期类型,Date是数据库日期类型
    exam_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="考试日期"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name="fk_exams_course_id",
            ondelete="RESTRICT"
        ),
        UniqueConstraint(
            "course_id",
            "id",
            name="uq_exams_course_id_id"
        ),
        Index(
           "ix_exams_course_date",
            "course_id",
            "exam_date"
        ),
    )

class ScopeDraft(Base):
    """"考试范围草稿，每场考试只有当前一份草稿"""

    __tablename__ = "scope_drafts"

    # 所属考试id,同时作为主键
    exam_id:Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exams.id" , ondelete="RESTRICT"),
        primary_key=True,
        comment="所属考试id"
    )

    draft_version:Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="草稿版本号"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint(
            "draft_version >= 1",
            name="ck_scope_draft_version"
        ),
    )


class ScopeDraftItem(Base):
    """考试范围草稿条目，记录每个知识点是否被纳入考试范围。"""

    __tablename__ = "scope_draft_items"

    # 所属考试ID
    exam_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("scope_drafts.exam_id", ondelete="CASCADE"),
        primary_key=True,
        comment="所属考试ID"
    )

    # 对应知识点ID
    # RESTRICT（默认） 存在关联子记录 -> 禁止删除主记录，报错
    point_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("knowledge_points.id", ondelete="RESTRICT"),
        primary_key=True,
        comment="知识点ID"
    )

    # 是否纳入考试范围
    included: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="是否考察该知识点"
    )

    # 考试优先级
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="知识点优先级"
    )

    __table_args__ = (
        CheckConstraint(
            "priority >= 0",
            name="ck_scope_draft_item_priority"
        ),
    )


# class ScopeDraft(Base):
#     """考试范围草稿，每场考试只有一份当前草稿"""

#     __tablename__ = "scope_drafts"

#     # 所属考试ID，同时作为主键
#     exam_id:Mapped[str] = mapped_column(
#         String(64),
#         ForeignKey("exams.id" , ondelete="RESTRICT"),
#         primary_key=True,
#         comment="所属考试ID"
#     )

#       草稿版本，用于防止多人或者多个请求覆盖
    # draft_version: Mapped[int] = mapped_column(
    #     Integer,
    #     nullable=False,
    #     default=1,
    #     comment="草稿版本号"
    # )

    # __table_args__ = (
    #     CheckConstraint(
    #         "draft_version >= 1",
    #         name="ck_scope_draft_version"
    #     ),
    # )

class ScopeVersion(Base):
    """正式考试范围版本，确认后不可原地修改"""

    __tablename__ = "scope_versions"

    # 正式范围版本唯一ID
    id:Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="正式范围版本ID"
    )

    # 所属考试ID
    exam_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exams.id" , ondelete="RESTRICT"),
        nullable=False,
        comment="所属考试ID"
    )

    # 当前考试的第几个正式版本
    version_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="正式范围版本号"
    )

    # 确认时间
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="范围确认时间"
    )

    __table_args__ = (
        UniqueConstraint(
            "exam_id",
            "version_no",
            name="uq_scope_versions_exam_version"
        ),
    )

class ScopeItem(Base):
    """正式考试范围条目，保存确认时的知识点信息快照。"""

    __tablename__ = "scope_items"

    # 所属正式范围版本ID
    scope_version_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("scope_versions.id", ondelete="RESTRICT"),
        primary_key=True,
        comment="所属正式范围版本ID"
    )

    # 对应知识点ID
    point_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("knowledge_points.id", ondelete="RESTRICT"),
        primary_key=True,
        comment="知识点ID"
    )

    # 是否纳入考试范围
    included: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="是否考察该知识点"
    )

    # 考试优先级
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="知识点优先级"
    )

    # 确认考试范围时的知识点名称快照
    point_name_snapshot: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
        comment="确认时的知识点名称"
    )

    __table_args__ = (
        CheckConstraint(
            "priority >= 0",
            name="ck_scope_item_priority"
        ),
    )

class PointProfileEvent(Base):
    """知识点掌握状态变更历史，记录用户自评和 AI 建议的变化"""

    __tablename__ = "point_profile_events"

    # 事件唯一ID
    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="事件唯一ID"
    )

    # 用户ID
    user_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="用户ID"
    )

    # 知识点ID
    point_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="知识点ID"
    )

    # 修改的字段： self_status / ai_status
    field_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="修改的字段"
    )

    # 修改前的状态，AI给出的建议或者用户自评的状态
    old_value: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="修改前的状态"
    )

    # 修改后的状态，AI给出的建议或者用户自评的状态
    new_value: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
        comment="修改后的状态"
    )

    # 操作者:user | ai
    actor: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="操作者"
    )

    # 事件发生时间
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="事件发生时间"
    )

    __table_args__ = (

        ForeignKeyConstraint(
        ["user_id" , "point_id"],
        ["user_point_profiles.user_id",
         "user_point_profiles.point_id"],
         name="fk_point_profile_events_profile",
         ondelete="RESTRICT"
        ),
        # filed_name：标记本次修改的是哪一行, IN ('self_status', 'ai_status'):是只能在self_status和ai_status之间选择一个，不能随便写别的
        # 防止站脏数据：比如代码写错了传了 xxx_status 直接数据库拦截
        CheckConstraint(
            "field_name IN ('self_status', 'ai_status')",
            name="ck_point_event_field"
        ),

        # 检查操作人
        CheckConstraint(
            "actor IN ('user', 'ai')",
            name="ck_point_event_actor"
        ),

        # old_value:变更前的状态值，可选的状态枚举: nor_started(未开始) / not_mastered(未掌握) / basic(基础掌握) / mastered(熟练掌握)
        CheckConstraint(
            "old_value IS NULL OR old_value IN"
            "('not_started', 'not_mastered', 'basic', 'mastered')",
            name="ck_point_event_old_value"
        ),
        CheckConstraint(
            "new_value IN "
            "('not_started', 'not_mastered', 'basic', 'mastered')",
            name="ck_profile_event_new_value"
        ),

        # ck_profile_event_actor_field:核心业务规则
        # 权限隔离规则
        # 用户(user)只能修改self_status(自自己的评估)
        # AI(ai)只能修改ai_status(AI给出的建议)
        CheckConstraint(
            "(field_name = 'self_status' AND actor = 'user') OR "
            "(field_name = 'ai_status' AND actor = 'ai')",
            name="ck_profile_event_actor_field"
        ),
        # 联合索引：(user_id, point_id, created_at)
        # 高频查询场景：查询某个用户、某个知识点，按时间顺序拉取全部变更历史
        # 左前缀也支持：查一个用户所有知识点变更；查用户 + 知识点的事件
        # `created_at` 放在最后，天然支持 order by created_at，不用额外排序文件排序，是事件表标准索引方案。
        Index(
            "ix_profile_events_user_point_created",
            "user_id",
            "point_id",
            "occurred_at"
        ),
    )


class Source(Base):
    """课程下登记的链接或笔记；正文提取属于后续任务。"""

    __tablename__ = "sources"
    __table_args__ = (
        CheckConstraint("kind IN ('link', 'note')", name="ck_sources_kind"),
        CheckConstraint("status = 'registered'", name="ck_sources_status"),
        CheckConstraint(
            "(kind = 'link' AND uri IS NOT NULL AND note_text IS NULL) OR "
            "(kind = 'note' AND note_text IS NOT NULL AND uri IS NULL)",
            name="ck_sources_payload",
        ),
        Index("ix_sources_course_created", "course_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    course_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    uri: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    note_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="registered")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
