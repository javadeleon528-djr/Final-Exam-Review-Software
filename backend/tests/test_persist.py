# test_persist.py
from datetime import datetime, UTC
from sqlalchemy.orm import Session
import uuid
from db import make_engine
from models import Course

# 共用同一个数据库地址，只写一次
DB_URL = "sqlite:///data/study.db"

# 1. 第一次连接，插入测试课程
engine = make_engine(DB_URL)
saved_id = None
with Session(engine) as session:
    test_course = Course(
        id=str(uuid.uuid4()),
        name="Python数据库开发",
        description="SQLAlchemy + Alembic小组项目课程",
        created_at=datetime.now(UTC),
        archived_at=None
    )
    session.add(test_course)
    session.commit()
    saved_id = test_course.id
    print(f"✅ 插入成功，课程id：{saved_id}")

# 释放第一个engine，模拟断开连接
del engine

# 2. 重新创建新engine、重连数据库
engine2 = make_engine(DB_URL)
with Session(engine2) as session2:
    find_course = session2.get(Course, saved_id)
    # assert 断言：不满足条件直接报错，程序不会正常退出
    assert find_course is not None, "❌ 重连后没有找到课程！持久化失败"
    assert find_course.id == saved_id, "❌ 查询出来的id对不上！"
    assert find_course.name == "Python数据库开发", "❌ 课程名称不一致！"

    print("✅ 断言全部通过！重连后成功查到课程：")
    print(f"id: {find_course.id}")
    print(f"name: {find_course.name}")
    print(f"created_at: {find_course.created_at}")
