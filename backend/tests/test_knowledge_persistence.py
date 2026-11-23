"""验证知识档案在迁移、重连和并发版本冲突下的行为。"""

import tempfile
import unittest
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.connection import make_engine
from app.db.models import Course, KnowledgePoint, UserPointProfile
from app.repositories.learning import (
    create_course,
    create_point,
    get_profile,
    list_points,
    update_self_status,
)


class TestKnowledgePersistence(unittest.TestCase):
    def test_profile_survives_reconnect_and_version_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_url = f"sqlite:///{(Path(temp_dir) / 'study.db').as_posix()}"
            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            config.set_main_option("sqlalchemy.url", db_url)
            command.upgrade(config, "head")

            engine = make_engine(db_url)
            try:
                self.assertIn("user_point_profiles", inspect(engine).get_table_names())
                with Session(engine) as session:
                    create_course(session, Course(id="course_1", name="高等数学"))
                    create_point(session, KnowledgePoint(
                        id="chapter_1", course_id="course_1", node_type="chapter", name="函数与极限"
                    ))
                    create_point(session, KnowledgePoint(
                        id="point_1", course_id="course_1", parent_id="chapter_1",
                        node_type="point", name="函数的极限"
                    ))
                    self.assertIsNone(get_profile(session, "chapter_1"))
                    session.commit()
            finally:
                engine.dispose()

            engine = make_engine(db_url)
            try:
                with Session(engine) as session:
                    self.assertEqual([point.id for point in list_points(session, "course_1")], ["chapter_1", "point_1"])
                    profile = get_profile(session, "point_1")
                    self.assertEqual((profile.self_status, profile.version), ("not_started", 1))
                    profile.ai_status = "not_mastered"
                    session.commit()

                    updated = update_self_status(session, "point_1", "basic", 1)
                    self.assertEqual((updated.self_status, updated.version), ("basic", 2))
                    self.assertEqual(updated.ai_status, "not_mastered")
                    self.assertIsNone(update_self_status(session, "point_1", "mastered", 1))
                    session.commit()

                command.upgrade(config, "head")
                with Session(engine) as session:
                    profile = get_profile(session, "point_1")
                    self.assertEqual((profile.self_status, profile.ai_status, profile.version),
                                     ("basic", "not_mastered", 2))
            finally:
                engine.dispose()

    def test_foreign_key_rejects_missing_point(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_url = f"sqlite:///{(Path(temp_dir) / 'study.db').as_posix()}"
            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            config.set_main_option("sqlalchemy.url", db_url)
            command.upgrade(config, "head")
            engine = make_engine(db_url)
            try:
                with Session(engine) as session:
                    self.assertEqual(session.execute(text("PRAGMA foreign_keys")).scalar_one(), 1)
                    session.add(UserPointProfile(user_id="local_user", point_id="missing"))
                    with self.assertRaises(IntegrityError):
                        session.commit()
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
