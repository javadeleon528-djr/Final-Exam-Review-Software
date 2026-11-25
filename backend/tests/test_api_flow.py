"""接口层端到端测试：课程 → 知识点 → 自评 → 考试 → 范围草稿 → 确认。"""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.db.connection import make_engine
from app.db.models import Base
from app.main import app
from app.services import course_service, exam_service, point_service, scope_service


class TestApiFlow(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        url = f"sqlite:///{(Path(self.tmp.name) / 'api.db').as_posix()}"
        self.engine = make_engine(url)
        Base.metadata.create_all(self.engine)
        for module in (course_service, point_service, exam_service, scope_service):
            module.engine = self.engine
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.engine.dispose()
        self.tmp.cleanup()

    def test_full_flow(self) -> None:
        c = self.client

        r = c.post("/api/v1/courses", json={"name": "高等数学"},
                   headers={"Idempotency-Key": "c1"})
        self.assertEqual(r.status_code, 201)
        course_id = r.json()["data"]["id"]

        r = c.post(f"/api/v1/courses/{course_id}/points",
                   json={"name": "第一章", "node_type": "chapter"},
                   headers={"Idempotency-Key": "p1"})
        self.assertEqual(r.status_code, 201)
        chapter = r.json()["data"]
        self.assertIsNone(chapter["self_status"])
        self.assertIsNone(chapter["version"])

        r = c.post(f"/api/v1/courses/{course_id}/points",
                   json={"name": "极限", "node_type": "point", "parent_id": chapter["id"]},
                   headers={"Idempotency-Key": "p2"})
        self.assertEqual(r.status_code, 201)
        point = r.json()["data"]
        self.assertEqual(point["self_status"], "not_started")
        self.assertEqual(point["version"], 1)

        r = c.get(f"/api/v1/courses/{course_id}/points")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["data"]["points"]), 2)

        r = c.put(f"/api/v1/points/{point['id']}/self-status",
                  json={"self_status": "basic", "expected_version": 1},
                  headers={"Idempotency-Key": "p3"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["self_status"], "basic")
        self.assertEqual(r.json()["data"]["version"], 2)

        r = c.put(f"/api/v1/points/{point['id']}/self-status",
                  json={"self_status": "mastered", "expected_version": 1},
                  headers={"Idempotency-Key": "p4"})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "VERSION_CONFLICT")

        r = c.post(f"/api/v1/courses/{course_id}/exams",
                   json={"name": "期中考试", "exam_date": "2026-12-20"},
                   headers={"Idempotency-Key": "e1"})
        self.assertEqual(r.status_code, 201)
        exam = r.json()["data"]
        self.assertEqual(exam["exam_date"], "2026-12-20")
        exam_id = exam["id"]

        r = c.get(f"/api/v1/exams/{exam_id}/scope-draft")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["draft_version"], 0)
        self.assertEqual(r.json()["data"]["items"], [])

        r = c.put(f"/api/v1/exams/{exam_id}/scope-draft",
                  json={"expected_version": 0, "items": [
                      {"point_id": point["id"], "included": True, "priority": "important"}]},
                  headers={"Idempotency-Key": "s1"})
        self.assertEqual(r.status_code, 200)
        draft = r.json()["data"]
        self.assertEqual(draft["draft_version"], 1)
        self.assertEqual(draft["included_count"], 1)
        self.assertEqual(draft["important_count"], 1)
        self.assertEqual(draft["items"][0]["priority"], "important")

        r = c.put(f"/api/v1/exams/{exam_id}/scope-draft",
                  json={"expected_version": 0, "items": []},
                  headers={"Idempotency-Key": "s2"})
        self.assertEqual(r.status_code, 409)

        r = c.post(f"/api/v1/exams/{exam_id}/scope-confirmations",
                   json={"expected_draft_version": 1},
                   headers={"Idempotency-Key": "cf1"})
        self.assertEqual(r.status_code, 201)
        scope = r.json()["data"]
        self.assertEqual(scope["scope_version"], 1)
        self.assertEqual(scope["items"][0]["priority"], "important")
        self.assertEqual(c.get(f"/api/v1/exams/{exam_id}/scope").status_code, 200)
        self.assertEqual(c.get(f"/api/v1/exams/{exam_id}/scope?version=1").status_code, 200)
        self.assertEqual(c.get(f"/api/v1/exams/{exam_id}/scope?version=99").status_code, 404)
        r = c.put(f"/api/v1/exams/{exam_id}/scope-draft",
                  json={"expected_version": 1, "items": []},
                  headers={"Idempotency-Key": "s3"})
        self.assertEqual(r.status_code, 200)
        r = c.post(f"/api/v1/exams/{exam_id}/scope-confirmations",
                   json={"expected_draft_version": 2},
                   headers={"Idempotency-Key": "cf2"})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["error"]["code"], "PLAN_INVALID")

    def test_not_found_and_missing_header(self) -> None:
        c = self.client
        self.assertEqual(c.get("/api/v1/courses/nope/points").status_code, 404)
        self.assertEqual(c.get("/api/v1/exams/nope/scope-draft").status_code, 404)
        self.assertEqual(c.get("/api/v1/exams/nope/scope").status_code, 404)

        r = c.post("/api/v1/courses", json={"name": "无头"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "VALIDATION_ERROR")


if __name__ == "__&#8203;main__":
    unittest.main()
