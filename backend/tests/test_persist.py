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
from app.db.models import Course


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


if __name__ == "__main__":
    unittest.main()
