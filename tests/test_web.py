"""Phase 2 dashboard tests."""

import unittest

from fastapi.testclient import TestClient

from src.storage.db import db_session, init_db, log_activity
from src.web.app import create_app


class WebAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = init_db()
        with db_session(self.db_path) as conn:
            log_activity(conn, "Test event", event_type="system")
        self.client = TestClient(create_app())

    def test_health(self) -> None:
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_dashboard_home(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Live dashboard", resp.text)
        self.assertIn("Activity log", resp.text)

    def test_activity_feed_partial(self) -> None:
        resp = self.client.get("/activity/feed")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Test event", resp.text)


if __name__ == "__main__":
    unittest.main()
