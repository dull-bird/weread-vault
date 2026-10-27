from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from weread_vault import cli
from weread_vault.db import connect, initialize


class RecordingGateway:
    """Captures the last gateway call so CLI argument mapping can be asserted."""

    calls: list[tuple[str, dict[str, object]]] = []

    def call(self, endpoint, **params):
        RecordingGateway.calls.append((endpoint, params))
        if endpoint == "/_list":
            return {"apis": [{"api_name": "/book/info", "description": "书籍信息",
                              "params": [{"name": "bookId", "required": True}]}]}
        return {"endpoint": endpoint, "params": params}

    def __init__(self, *a, **k):
        pass


class CliApiTests(unittest.TestCase):
    def setUp(self):
        RecordingGateway.calls = []
        patcher = mock.patch.object(cli, "Gateway", RecordingGateway)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _run(self, argv):
        out = io.StringIO()
        with redirect_stdout(out):
            cli.main(argv)
        return out.getvalue()

    def test_api_passthrough_coerces_numbers_but_keeps_ids_as_strings(self):
        self._run(["api", "/store/search", "keyword=三体", "count=5", "bookId=635722"])
        endpoint, params = RecordingGateway.calls[-1]
        self.assertEqual(endpoint, "/store/search")
        self.assertEqual(params["keyword"], "三体")
        self.assertEqual(params["count"], 5)  # numeric -> int
        self.assertEqual(params["bookId"], "635722")  # id-like -> stays string

    def test_search_maps_to_store_search(self):
        self._run(["search", "三体", "--count", "3"])
        endpoint, params = RecordingGateway.calls[-1]
        self.assertEqual(endpoint, "/store/search")
        self.assertEqual(params, {"keyword": "三体", "count": 3})

    def test_book_popular_maps_to_bestbookmarks_with_string_id(self):
        self._run(["book", "635722", "popular"])
        endpoint, params = RecordingGateway.calls[-1]
        self.assertEqual(endpoint, "/book/bestbookmarks")
        self.assertEqual(params, {"bookId": "635722"})

    def test_book_reviews_includes_count(self):
        self._run(["book", "635722", "reviews", "--count", "7"])
        endpoint, params = RecordingGateway.calls[-1]
        self.assertEqual(endpoint, "/review/list")
        self.assertEqual(params, {"bookId": "635722", "count": 7})

    def test_apis_lists_endpoints(self):
        output = self._run(["apis"])
        self.assertIn("/book/info", output)
        self.assertIn("必填：bookId", output)

    def test_bad_kv_param_raises(self):
        with self.assertRaises(SystemExit):
            self._run(["api", "/x", "notakeyvalue"])

    def test_open_uses_db_link_or_fetches_book_info_or_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "vault.db"
            initialize(db_path)
            with connect(db_path) as conn:
                conn.execute(
                    "INSERT INTO books(book_id,title,author,reader_link,synced_at)"
                    " VALUES('b1','三体','刘慈欣','https://weread.qq.com/web/reader/r1',0)"
                )
                conn.execute(
                    "INSERT INTO books(book_id,title,author,synced_at) VALUES('b2','流浪地球','刘慈欣',0)"
                )
                conn.execute(
                    "INSERT INTO books(book_id,title,author,synced_at) VALUES('b3','无链接书','作者',0)"
                )

            with mock.patch.object(cli.platform, "system", return_value="Linux"):
                out = self._run(["--db", str(db_path), "open", "b1"])
                self.assertIn("https://weread.qq.com/web/reader/r1", out)
                self.assertEqual(len(RecordingGateway.calls), 0)

                # b2 has no link in DB -> fetches /book/info once and stores it
                orig_call = RecordingGateway.call
                def fake_call(gw, endpoint, **params):
                    RecordingGateway.calls.append((endpoint, params))
                    if endpoint == "/book/info" and params.get("bookId") == "b2":
                        return {"deepLink": "https://weread.qq.com/web/bookDetail/d2"}
                    return {}
                with mock.patch.object(RecordingGateway, "call", fake_call):
                    out2 = self._run(["--db", str(db_path), "open", "b2"])
                    self.assertIn("https://weread.qq.com/web/bookDetail/d2", out2)
                    with connect(db_path) as conn:
                        saved = conn.execute("SELECT deep_link FROM books WHERE book_id='b2'").fetchone()[0]
                        self.assertEqual(saved, "https://weread.qq.com/web/bookDetail/d2")

                    # b3 has no link in DB and /book/info returns none -> exits non-zero with message
                    err = io.StringIO()
                    with redirect_stderr(err), self.assertRaises(SystemExit) as ctx:
                        self._run(["--db", str(db_path), "open", "b3"])
                    self.assertNotEqual(ctx.exception.code, 0)
                    self.assertIn("官方没有给这本书的链接", err.getvalue())

    def test_query_book_status_view_and_stats_reading_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "vault.db"
            initialize(db_path)
            with connect(db_path) as conn:
                conn.execute(
                    "INSERT INTO books(book_id,title,author,progress,finished,reading_seconds,finish_time,synced_at)"
                    " VALUES('b1','已读书A','作者1',100,1,3600,1700000000,0)"
                )
                conn.execute(
                    "INSERT INTO books(book_id,title,author,progress,finished,reading_seconds,finish_time,synced_at)"
                    " VALUES('b2','已读书B','作者2',20,1,1800,1710000000,0)"
                )
                conn.execute(
                    "INSERT INTO books(book_id,title,author,progress,finished,reading_seconds,synced_at)"
                    " VALUES('b3','在读书','作者3',45,0,1800,0)"
                )
                conn.execute(
                    "INSERT INTO books(book_id,title,author,progress,finished,reading_seconds,synced_at)"
                    " VALUES('b4','未读书','作者4',0,0,0,0)"
                )

            schema_out = json.loads(self._run(["--db", str(db_path), "query", "--schema"]))
            self.assertIn("book_status", schema_out["tables"])
            rows = json.loads(
                self._run(["--db", str(db_path), "query", "SELECT book_id, status FROM book_status ORDER BY book_id"])
            )
            self.assertEqual(
                rows,
                [
                    {"book_id": "b1", "status": "已读"},
                    {"book_id": "b2", "status": "已读"},
                    {"book_id": "b3", "status": "在读"},
                    {"book_id": "b4", "status": "未读"},
                ],
            )
            stats_out = json.loads(self._run(["--db", str(db_path), "stats"]))
            rs = stats_out["reading_status"]
            self.assertEqual(rs["已读"], 2)
            self.assertEqual(rs["在读"], 1)
            self.assertEqual(rs["未读"], 1)
            self.assertEqual(rs["reading_hours"], 2.0)
            self.assertEqual([item["title"] for item in rs["recent_finished"]], ["已读书B", "已读书A"])
            self.assertTrue(rs["recent_finished"][0]["date"])


if __name__ == "__main__":
    unittest.main()
