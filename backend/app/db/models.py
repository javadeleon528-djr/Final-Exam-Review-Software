from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime
from datetime import datetime

# 基础父类，所有表都继承它。
class Base(DeclarativeBase):
    pass

# Course 模型与课程接口的字段保持一致。
class Course(Base):
    __tablename__ = "courses"

    # id 是稳定的字符串标识，由创建课程的业务逻辑生成。
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
