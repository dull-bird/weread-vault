from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from weread_vault import web
from weread_vault.db import connect, initialize


class NormAuthorTests(unittest.TestCase):
    def test_strips_brackets_and_matches_by_equality(self):
        n = web._norm_author
        self.assertEqual(n("[日]斋藤康毅"), n("斋藤康毅"))
        self.assertEqual(n("弗兰克·扬纳斯"), n("[美]弗兰克·扬纳斯"))
        # a shorter name must NOT equal a different longer one (the 弗兰克扬 mis-match bug)
        self.assertNotEqual(n("弗兰克扬"), n("[美]弗兰克·扬纳斯"))


class WebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "vault.db"
        initialize(self.db_path)
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO books(book_id, title, author, cover, total_notes, reading_progress, sort, synced_at)"
                " VALUES('book-1', 'Test Book', 'Author', 'https://example.test/cover.jpg', 2, 33, 99, 0)"
            )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), web.make_handler(self.db_path))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def get_json(self, path: str):
        with urllib.request.urlopen(f"{self.base_url}{path}") as response:
            return json.loads(response.read().decode("utf-8"))

    def test_books_api_includes_cover(self):
        rows = self.get_json("/api/books?limit=1")
        self.assertEqual(rows[0]["title"], "Test Book")
        self.assertEqual(rows[0]["cover"], "https://example.test/cover.jpg")

    def test_stats_endpoint_parses_overall_snapshot(self):
        payload = {
            "totalReadTime": 3600, "readDays": 10, "authorCount": 5,
            "readTimes": {"1514736000": 1000, "1546272000": 2000},  # 2018, 2019
            "preferTime": list(range(24)),
            "preferCategory": [{"categoryTitle": "经济理财", "readingTime": 500, "readingCount": 3}],
            "preferAuthor": [{"name": "刘慈欣", "count": 2, "readTime": "1小时"}],
            "readStat": [{"stat": "读过", "counts": "10本"}],
            "preferCategoryWord": "偏好经济理财",
        }
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO reading_stats(mode, base_time, payload, fetched_at) VALUES('overall', 0, ?, 100)",
                (json.dumps(payload),),
            )
            conn.execute(
                "INSERT INTO reading_stats(mode, base_time, payload, fetched_at) VALUES('weekly', 0, ?, 101)",
                (json.dumps({"totalReadTime": 60, "readDays": 1, "readTimes": {"1782057600": 60}}),),
            )
        data = self.get_json("/api/stats")
        self.assertTrue(data["hasData"])
        overall = data["overall"]
        self.assertEqual(overall["totalReadTime"], 3600)
        self.assertEqual([y["label"] for y in overall["byYear"]], [2018, 2019])
        self.assertEqual(overall["categories"][0]["title"], "经济理财")
        self.assertEqual(len(overall["preferTime"]), 24)
        self.assertEqual(len(data["periods"]["overall"]["preferTime"]), 24)
        self.assertEqual(data["periods"]["overall"]["authors"][0]["name"], "刘慈欣")
        self.assertEqual(data["byDayWeek"][0]["seconds"], 60)

    def test_stats_endpoint_estimates_missing_time_and_authors_from_highlights(self):
        now = int(time.time())
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO reading_stats(mode, base_time, payload, fetched_at) VALUES('overall', 0, ?, 100)",
                (json.dumps({"totalReadTime": 1, "readDays": 1}),),
            )
            conn.execute(
                "INSERT INTO reading_stats(mode, base_time, payload, fetched_at) VALUES('weekly', 0, ?, 101)",
                (json.dumps({"totalReadTime": 1, "readDays": 1}),),
            )
            conn.execute(
                """INSERT INTO highlights(bookmark_id,book_id,chapter_uid,chapter_title,mark_text,text_range,create_time,updated_at)
                VALUES('mark-1','book-1',1,'Chapter','A highlight','1',?,?)""",
                (now, now),
            )
        data = self.get_json("/api/stats")
        weekly = data["periods"]["weekly"]
        self.assertEqual(weekly["preferTimeSource"], "划线时间估算")
        self.assertGreater(sum(weekly["preferTime"]), 0)
        self.assertEqual(weekly["authorsSource"], "划线时间估算")
        self.assertEqual(weekly["authors"][0]["name"], "Author")
        self.assertEqual(weekly["authors"][0]["readTime"], "1 条划线")
        self.assertEqual(weekly["categoriesSource"], "划线时间估算")
        self.assertEqual(weekly["categories"][0]["title"], "未分类")
        self.assertEqual(weekly["categories"][0]["seconds"], 1)

    def test_stats_endpoint_reports_no_data_when_empty(self):
        self.assertEqual(self.get_json("/api/stats"), {"hasData": False})

    def test_sync_endpoint_defaults_to_full_pipeline_with_reconcile(self):
        calls: list[str] = []
        original_gateway = web.Gateway
        original_sync_service = web.SyncService

        class FakeGateway:
            pass

        class FakeSyncService:
            def __init__(self, conn, gateway, report=print):
                calls.append(type(gateway).__name__)

            def all(self, full_notes=False, note_limit=None):
                calls.append(f"all:{full_notes}")
                return {"shelf": 5, "books": 1, "removed": 2, "notes": 3, "stats": 4}

        try:
            web.Gateway = FakeGateway
            web.SyncService = FakeSyncService
            request = urllib.request.Request(f"{self.base_url}/api/sync", method="POST")
            with urllib.request.urlopen(request) as response:
                body = json.loads(response.read().decode("utf-8"))
            self.assertEqual(body, {"status": "ok", "mode": "notes",
                                    "counts": {"shelf": 5, "books": 1, "removed": 2, "notes": 3, "stats": 4}})
            self.assertEqual(calls, ["FakeGateway", "all:False"])
        finally:
            web.Gateway = original_gateway
            web.SyncService = original_sync_service

    def test_sync_endpoint_books_mode_reconciles_without_notes(self):
        calls: list[str] = []
        original_sync_service = web.SyncService

        class FakeSyncService:
            def __init__(self, conn, gateway, report=print):
                pass

            def shelf(self):
                calls.append("shelf")
                return 7

            def books(self):
                calls.append("books")
                return 9

            def reconcile(self):
                calls.append("reconcile")
                return 3

        try:
            web.SyncService = FakeSyncService
            request = urllib.request.Request(
                f"{self.base_url}/api/sync",
                data=json.dumps({"mode": "books"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request) as response:
                body = json.loads(response.read().decode("utf-8"))
            self.assertEqual(body, {"status": "ok", "mode": "books",
                                    "counts": {"shelf": 7, "books": 9, "removed": 3, "notes": 0, "stats": 0}})
            self.assertEqual(calls, ["shelf", "books", "reconcile"])
        finally:
            web.SyncService = original_sync_service

    def test_settings_endpoint_reports_key_source_without_value(self):
        original_api_key_source = web.api_key_source
        original_default_config_path = web.default_config_path
        try:
            web.api_key_source = lambda: "config"
            web.default_config_path = lambda: self.db_path.parent / "config.json"
            body = self.get_json("/api/settings")
            self.assertEqual(body["source"], "config")
            self.assertTrue(body["api_key_configured"])
            self.assertNotIn("api_key", body)
            self.assertNotIn("weread_api_key", body)
        finally:
            web.api_key_source = original_api_key_source
            web.default_config_path = original_default_config_path

    def test_save_api_key_endpoint_uses_private_config_writer(self):
        saved: list[str] = []
        original_save_api_key = web.save_api_key
        try:
            web.save_api_key = lambda api_key: saved.append(api_key) or (self.db_path.parent / "config.json")
            request = urllib.request.Request(
                f"{self.base_url}/api/settings/api-key",
                data=json.dumps({"api_key": "wrk-test"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request) as response:
                body = json.loads(response.read().decode("utf-8"))
            self.assertEqual(body["status"], "ok")
            self.assertEqual(saved, ["wrk-test"])
            self.assertNotIn("wrk-test", json.dumps(body))
        finally:
            web.save_api_key = original_save_api_key


if __name__ == "__main__":
    unittest.main()
