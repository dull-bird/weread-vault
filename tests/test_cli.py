from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from weread_vault import cli


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


if __name__ == "__main__":
    unittest.main()
