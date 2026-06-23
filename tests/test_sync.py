from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from weread_vault.db import connect, initialize
from weread_vault.sync import SyncService


class FakeGateway:
    sleep_seconds = 0

    def __init__(self, fail_reviews: bool = False):
        self.fail_reviews = fail_reviews

    def call(self, endpoint, **params):
        if endpoint == "/user/notebooks":
            return {
                "hasMore": 0,
                "books": [{"bookId": "book-1", "sort": 99, "noteCount": 1, "reviewCount": 1,
                           "bookmarkCount": 0, "readingProgress": 10,
                           "book": {"title": "Test Book", "author": "Author", "categories": []}}],
            }
        if endpoint == "/book/bookmarklist":
            return {"chapters": [{"chapterUid": 1, "title": "Chapter"}], "updated": [
                {"bookmarkId": "mark-1", "chapterUid": 1, "markText": "A highlight", "range": "1", "createTime": 1}
            ]}
        if endpoint == "/review/list/mine":
            if self.fail_reviews:
                raise RuntimeError("network failed")
            return {"hasMore": 0, "reviews": [{"review": {
                "reviewId": "review-1", "content": "A thought", "chapterName": "Chapter", "chapterUid": 1, "createTime": 2
            }}]}
        if endpoint == "/readdata/detail":
            return {"ok": True}
        if endpoint == "/shelf/sync":
            return {"books": [
                {"bookId": "book-1", "title": "Test Book", "author": "Author", "cover": "c1", "category": "文学"},
                {"bookId": "book-2", "title": "Shelf Only", "author": "B", "cover": "c2",
                 "category": "科技", "finishReading": 1, "updateTime": 50},
            ]}
        raise AssertionError(endpoint)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "vault.db"
        initialize(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_failed_book_does_not_advance_watermark(self):
        with connect(self.db_path) as conn:
            service = SyncService(conn, FakeGateway(), report=lambda _: None)
            service.books()
            service = SyncService(conn, FakeGateway(fail_reviews=True), report=lambda _: None)
            with self.assertRaises(RuntimeError):
                service.notes()
            book = conn.execute("SELECT notes_synced_sort FROM books WHERE book_id='book-1'").fetchone()
            self.assertIsNone(book["notes_synced_sort"])
            self.assertEqual(conn.execute("SELECT count(*) FROM highlights").fetchone()[0], 0)

    def test_shelf_sync_adds_all_books_without_clobbering_noted_books(self):
        with connect(self.db_path) as conn:
            service = SyncService(conn, FakeGateway(), report=lambda _: None)
            service.books()  # book-1 gets total_notes from notebooks
            service.notes()
            noted_before = conn.execute("SELECT total_notes FROM books WHERE book_id='book-1'").fetchone()[0]
            self.assertEqual(service.shelf(), 2)
            # shelf-only book added with zero notes
            shelf_only = conn.execute("SELECT total_notes,finished FROM books WHERE book_id='book-2'").fetchone()
            self.assertEqual(shelf_only["total_notes"], 0)
            self.assertEqual(shelf_only["finished"], 1)
            # existing noted book keeps its note count (shelf sync is non-destructive)
            noted_after = conn.execute("SELECT total_notes FROM books WHERE book_id='book-1'").fetchone()[0]
            self.assertEqual(noted_after, noted_before)

    def test_successful_book_is_atomic_and_searchable(self):
        with connect(self.db_path) as conn:
            service = SyncService(conn, FakeGateway(), report=lambda _: None)
            service.books()
            self.assertEqual(service.notes(), 1)
            book = conn.execute("SELECT notes_synced_sort FROM books WHERE book_id='book-1'").fetchone()
            self.assertEqual(book["notes_synced_sort"], 99)
            self.assertEqual(conn.execute("SELECT count(*) FROM highlights").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT count(*) FROM thoughts").fetchone()[0], 1)
