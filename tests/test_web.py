from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from weread_vault import web
from weread_vault.db import connect, initialize


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

    def test_sync_endpoint_defaults_to_incremental_notes(self):
        calls: list[str] = []
        original_gateway = web.Gateway
        original_sync_service = web.SyncService

        class FakeGateway:
            pass

        class FakeSyncService:
            def __init__(self, conn, gateway, report=print):
                calls.append(type(gateway).__name__)

            def books(self):
                calls.append("books")
                return 1

            def notes(self, full=False):
                calls.append(f"notes:{full}")
                return 2

            def stats(self):
                calls.append("stats")
                return 3

        try:
            web.Gateway = FakeGateway
            web.SyncService = FakeSyncService
            request = urllib.request.Request(f"{self.base_url}/api/sync", method="POST")
            with urllib.request.urlopen(request) as response:
                body = json.loads(response.read().decode("utf-8"))
            self.assertEqual(body, {"status": "ok", "mode": "notes", "counts": {"books": 1, "notes": 2, "stats": 3}})
            self.assertEqual(calls, ["FakeGateway", "books", "notes:False", "stats"])
        finally:
            web.Gateway = original_gateway
            web.SyncService = original_sync_service

    def test_sync_endpoint_supports_books_only_mode(self):
        calls: list[str] = []
        original_sync_service = web.SyncService

        class FakeSyncService:
            def __init__(self, conn, gateway, report=print):
                pass

            def books(self):
                calls.append("books")
                return 9

            def notes(self, full=False):
                calls.append("notes")
                return 0

            def stats(self):
                calls.append("stats")
                return 0

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
            self.assertEqual(body, {"status": "ok", "mode": "books", "counts": {"books": 9, "notes": 0, "stats": 0}})
            self.assertEqual(calls, ["books"])
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
