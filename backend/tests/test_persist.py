"""验证课程数据在迁移、重连和重复迁移后仍然存在。"""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.db.connection import make_engine
from app.db.models import Course, KnowledgePoint


class TestCoursePersistence(unittest.TestCase):
    def test_course_survives_reconnect_and_repeat_migration(self) -> None:
        # 每次测试使用独立数据库，避免改动 data/study.db。
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_url = f"sqlite:///{db_path.as_posix()}"

            alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
            config = Config(str(alembic_ini))
            config.set_main_option("sqlalchemy.url", db_url)
            command.upgrade(config, "head")

            course_id = str(uuid4())
            engine = make_engine(db_url)
            try:
                self.assertIn("courses", inspect(engine).get_table_names())
                with Session(engine) as session:
                    session.add(
                        Course(
                            id=course_id,
                            name="Python数据库开发",
                            description="SQLAlchemy + Alembic 小组项目课程",
                            created_at=datetime.now(timezone.utc),
                            archived_at=None,
                        )
                    )
                    session.commit()
            finally:
                # Windows 下先关闭连接池，临时目录才能删除数据库文件。
                engine.dispose()

            engine_after_restart = make_engine(db_url)
            try:
                with Session(engine_after_restart) as session:
                    saved_course = session.get(Course, course_id)
                    self.assertIsNotNone(saved_course)
                    self.assertEqual(saved_course.name, "Python数据库开发")

                # 重复执行迁移不应重建表或丢失已有记录。
                command.upgrade(config, "head")
                with Session(engine_after_restart) as session:
                    saved_course = session.get(Course, course_id)
                    self.assertIsNotNone(saved_course)
                    self.assertEqual(saved_course.name, "Python数据库开发")
            finally:
                engine_after_restart.dispose()

        self.assertFalse(db_path.exists())


class TestKnowledgePointPersistence(unittest.TestCase):
    def test_knowledge_point_can_be_saved(self) -> None:
        # 每次测试使用独立数据库，避免改动 data/study.db。
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_url = f"sqlite:///{db_path.as_posix()}"

            # 执行数据库迁移，创建测试所需的数据表。
            alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
            config = Config(str(alembic_ini))
            config.set_main_option("sqlalchemy.url", db_url)
            command.upgrade(config, "head")

            # 生成课程ID和知识点ID。
            course_id = str(uuid4())
            kp_id = str(uuid4())

            engine = make_engine(db_url)
            try:
                # 检查 knowledge_points 表是否存在。
                self.assertIn("knowledge_points", inspect(engine).get_table_names())

                with Session(engine) as session:
                    # 先创建课程。
                    course = Course(
                        id=course_id,
                        name="Python程序设计",
                        description="数据库测试课程",
                        created_at=datetime.now(timezone.utc),
                        archived_at=None,
                    )

                    session.add(course)
                    session.flush()  # 把待处理的INSERT直接交给数据库，但不会提交事务

                    # 创建一个根知识点。
                    # parent_id=None是因为它是根节点
                    knowledge_point = KnowledgePoint(
                        id=kp_id,
                        course_id=course_id,
                        parent_id=None,
                        node_type="chapter",
                        name="第一章",
                    )

                    session.add(knowledge_point)
                    session.commit()

                # 从数据库重新读取知识点，验证是否保存成功。
                with Session(engine) as session:
                    saved_point = session.get(KnowledgePoint, kp_id)  # 为什么重新查询？我们要验证的是数据库中真的存在这条记录，而不是仅仅验证 Python 对象创建成功。

                    self.assertIsNotNone(saved_point)
                    self.assertEqual(saved_point.course_id, course_id)
                    self.assertEqual(saved_point.node_type, "chapter")
                    self.assertEqual(saved_point.name, "第一章")
                    self.assertIsNone(saved_point.parent_id)
                    self.assertEqual(saved_point.sort_order, 0)

            finally:
                # Windows 下先关闭连接池，临时目录才能删除数据库文件。
                engine.dispose()

        self.assertFalse(db_path.exists())


if __name__ == "__main__":
    unittest.main()
