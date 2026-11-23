"""考试范围版本、来源登记与知识档案事件的持久化验收。"""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.connection import make_engine
from app.db.models import Course, Exam, KnowledgePoint, PointProfileEvent, Source
from app.repositories.exams import (
    ScopeDraftVersionConflict, confirm_scope, create_exam,
    get_confirmed_scope, get_scope_draft, save_scope_draft,
)
from app.repositories.learning import create_course, create_point, get_profile, update_self_status
from app.repositories.sources import create_source, list_sources


class TestExamScope(unittest.TestCase):
    def test_independent_exams_keep_history_and_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            url = f"sqlite:///{(Path(temp_dir) / 'study.db').as_posix()}"
            cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            cfg.set_main_option("sqlalchemy.url", url)
            command.upgrade(cfg, "head")
            engine = make_engine(url)
            try:
                with Session(engine) as session:
                    create_course(session, Course(id="math", name="高数"))
                    create_course(session, Course(id="other", name="线代"))
                    for point_id, course_id in (("limit", "math"), ("derivative", "math"), ("matrix", "other")):
                        create_point(session, KnowledgePoint(
                            id=point_id, course_id=course_id, node_type="point", name=point_id
                        ))
                    create_exam(session, Exam(id="midterm", course_id="math", name="期中", exam_date=date(2027, 1, 1)))
                    create_exam(session, Exam(id="final", course_id="math", name="期末", exam_date=date(2027, 2, 1)))
                    session.commit()

                    with self.assertRaises(ValueError):
                        save_scope_draft(session, "final", 0, [("matrix", True, "normal")])
                    first = save_scope_draft(session, "final", 0, [
                        ("limit", True, "important"), ("derivative", False, "normal")
                    ])
                    self.assertEqual(first.draft_version, 1)
                    self.assertIsNotNone(first.updated_at)
                    with self.assertRaises(ScopeDraftVersionConflict):
                        save_scope_draft(session, "final", 0, [])
                    v1, entries1 = confirm_scope(session, "final", 1)
                    self.assertEqual(v1.version_no, 1)
                    self.assertCountEqual([(x.point_id, x.included, x.priority) for x in entries1],
                                          [("limit", True, 1), ("derivative", False, 0)])
                    session.commit()

                    save_scope_draft(session, "final", 1, [("derivative", True, "normal")])
                    v2, _ = confirm_scope(session, "final", 2)
                    self.assertEqual(v2.version_no, 2)
                    save_scope_draft(session, "midterm", 0, [("limit", True, "normal")])
                    confirm_scope(session, "midterm", 1)
                    update_self_status(session, "limit", "basic", 1)
                    session.commit()
            finally:
                engine.dispose()

            command.upgrade(cfg, "head")
            engine = make_engine(url)
            try:
                with Session(engine) as session:
                    old, old_entries = get_confirmed_scope(session, "final", 1)
                    latest, latest_entries = get_confirmed_scope(session, "final")
                    midterm, _ = get_confirmed_scope(session, "midterm")
                    self.assertEqual((old.version_no, latest.version_no, midterm.version_no), (1, 2, 1))
                    self.assertEqual(len(old_entries), 2)
                    self.assertEqual([i.point_id for i in latest_entries], ["derivative"])
                    self.assertEqual(get_profile(session, "limit").self_status, "basic")
                    events = list(session.scalars(select(PointProfileEvent)))
                    self.assertEqual((len(events), events[0].old_value, events[0].new_value),
                                     (1, "not_started", "basic"))
                    self.assertEqual(get_scope_draft(session, "final")[0].draft_version, 2)
            finally:
                engine.dispose()

    def test_sources_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            url = f"sqlite:///{(Path(temp_dir) / 'study.db').as_posix()}"
            cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            cfg.set_main_option("sqlalchemy.url", url)
            command.upgrade(cfg, "head")
            engine = make_engine(url)
            try:
                with Session(engine) as session:
                    create_course(session, Course(id="math", name="高数"))
                    create_source(session, Source(
                        id="link1", course_id="math", kind="link", title="课程网站",
                        uri="https://example.edu/math",
                    ))
                    create_source(session, Source(
                        id="note1", course_id="math", kind="note", title="笔记",
                        note_text="极限定义",
                    ))
                    session.commit()
                    self.assertEqual([s.id for s in list_sources(session, "math")], ["link1", "note1"])
                    create_source(session, Source(
                        id="temporary", course_id="math", kind="note", title="临时",
                        note_text="撤销",
                    ))
                    session.rollback()
                with Session(engine) as session:
                    self.assertEqual(len(list_sources(session, "math")), 2)
                    with self.assertRaises(ValueError):
                        create_source(session, Source(
                            id="bad", course_id="math", kind="link", title="错误",
                            uri="https://example.edu", note_text="混合内容",
                        ))
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
