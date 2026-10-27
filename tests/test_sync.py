from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from weread_vault.db import connect, initialize
from weread_vault.sync import SyncService


class FakeGateway:
    sleep_seconds = 0
    api_key = "fake-key"

    def __init__(self, fail_reviews: bool = False):
        self.fail_reviews = fail_reviews
        self.bookmark_calls: list[str] = []

    def call(self, endpoint, **params):
        if endpoint == "/book/bookmarklist":
            self.bookmark_calls.append(params.get("bookId"))
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
                "reviewId": "review-1", "content": "A thought", "abstract": "Original quote",
                "range": "10-20", "chapterName": "Chapter", "chapterUid": 1, "chapterIdx": 3, "createTime": 2
            }}]}
        if endpoint == "/readdata/detail":
            return {"ok": True}
        if endpoint == "/shelf/sync":
            return {"books": [
                {"bookId": "book-1", "title": "Test Book", "author": "Author", "cover": "c1", "category": "文学",
                 "readerLink": "https://weread.qq.com/web/reader/r1", "deepLink": "https://weread.qq.com/web/bookDetail/d1"},
                {"bookId": "book-2", "title": "Shelf Only", "author": "B", "cover": "c2",
                 "category": "科技", "finishReading": 1, "updateTime": 50,
                 "deepLink": "https://weread.qq.com/web/bookDetail/d2"},
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
            # existing noted book keeps its note count (shelf sync is non-destructive) and stores official links
            noted_after = conn.execute(
                "SELECT total_notes, reader_link, deep_link FROM books WHERE book_id='book-1'"
            ).fetchone()
            self.assertEqual(noted_after["total_notes"], noted_before)
            self.assertEqual(noted_after["reader_link"], "https://weread.qq.com/web/reader/r1")
            self.assertEqual(noted_after["deep_link"], "https://weread.qq.com/web/bookDetail/d1")

    def test_account_switch_removes_old_account_books_with_their_notes(self):
        with connect(self.db_path) as conn:
            # Seed a book (with a note) that belongs to a previous account and is NOT on the
            # current shelf / notebooks returned by FakeGateway.
            conn.execute("INSERT INTO books(book_id,title,total_notes,sort,synced_at) VALUES('old-1','旧账号的书',3,5,0)")
            conn.execute(
                "INSERT INTO highlights(bookmark_id,book_id,chapter_uid,chapter_title,mark_text,text_range,create_time,updated_at)"
                " VALUES('om1','old-1',1,'C','旧划线','1',1,0)")
            conn.commit()
            result = SyncService(conn, FakeGateway(), report=lambda _: None).all()
            self.assertEqual(result["removed"], 1)
            self.assertIsNone(conn.execute("SELECT 1 FROM books WHERE book_id='old-1'").fetchone())
            # its highlights cascade away; current-account books remain
            self.assertEqual(conn.execute("SELECT count(*) FROM highlights WHERE book_id='old-1'").fetchone()[0], 0)
            self.assertIsNotNone(conn.execute("SELECT 1 FROM books WHERE book_id='book-1'").fetchone())
            self.assertIsNotNone(conn.execute("SELECT 1 FROM books WHERE book_id='book-2'").fetchone())

    def test_on_shelf_flag_set_during_full_sync(self):
        with connect(self.db_path) as conn:
            # An off-shelf book (not returned by /shelf/sync nor /user/notebooks) is removed; the
            # shelf books from FakeGateway are flagged on_shelf=1.
            conn.execute("INSERT INTO books(book_id,title,total_notes,sort,synced_at) VALUES('ghost','x',0,1,0)")
            conn.commit()
            SyncService(conn, FakeGateway(), report=lambda _: None).all()
            shelf = {r[0]: r[1] for r in conn.execute("SELECT book_id,on_shelf FROM books")}
            self.assertEqual(shelf.get("book-1"), 1)
            self.assertEqual(shelf.get("book-2"), 1)
            self.assertNotIn("ghost", shelf)  # not on shelf / not noted → reconciled away

    def test_notes_skips_books_without_notes(self):
        with connect(self.db_path) as conn:
            gateway = FakeGateway()
            service = SyncService(conn, gateway, report=lambda _: None)
            service.shelf()  # adds book-1 and book-2 (book-2 has total_notes=0)
            service.books()  # book-1 gets notes from notebooks
            synced = service.notes()
            self.assertEqual(synced, 1)  # only book-1
            # book-2 (no notes) is never fetched
            self.assertNotIn("book-2", gateway.bookmark_calls)
            self.assertIn("book-1", gateway.bookmark_calls)

    def test_successful_book_is_atomic_and_searchable(self):
        with connect(self.db_path) as conn:
            service = SyncService(conn, FakeGateway(), report=lambda _: None)
            service.books()
            self.assertEqual(service.notes(), 1)
            book = conn.execute("SELECT notes_synced_sort FROM books WHERE book_id='book-1'").fetchone()
            self.assertEqual(book["notes_synced_sort"], 99)
            self.assertEqual(conn.execute("SELECT count(*) FROM highlights").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT count(*) FROM thoughts").fetchone()[0], 1)
            thought = conn.execute(
                "SELECT content, abstract, text_range, chapter_uid, chapter_idx FROM thoughts WHERE review_id='review-1'"
            ).fetchone()
            self.assertEqual(thought["content"], "A thought")
            self.assertEqual(thought["abstract"], "Original quote")
            self.assertEqual(thought["text_range"], "10-20")
            self.assertEqual(thought["chapter_uid"], 1)
            self.assertEqual(thought["chapter_idx"], 3)

    def test_reading_progress_sync_and_limit_and_book_status_view(self):
        progress_calls: list[str] = []

        class ProgressGateway(FakeGateway):
            def call(self, endpoint, **params):
                if endpoint == "/shelf/sync":
                    return {
                        "books": [
                            {"bookId": "b-fin", "title": "读完的书", "author": "A", "readUpdateTime": 300},
                            {"bookId": "b-read", "title": "在读的书", "author": "B", "readUpdateTime": 200},
                            {"bookId": "b-unr", "title": "未读的书", "author": "C", "readUpdateTime": 100},
                        ],
                        "albums": [{"albumInfo": {"albumId": "alb-1", "name": "有声书"}}],
                    }
                if endpoint == "/book/getprogress":
                    bid = params.get("bookId")
                    progress_calls.append(bid)
                    if bid == "b-fin":
                        return {"book": {"progress": 100, "finishTime": 1700000000,
                                         "recordReadingTime": 7200, "updateTime": 300}}
                    if bid == "b-read":
                        return {"book": {"progress": 35, "recordReadingTime": 1800, "updateTime": 200}}
                    if bid == "b-unr":
                        return {"book": {"progress": 0, "recordReadingTime": 0, "updateTime": 100}}
                return super().call(endpoint, **params)

        with connect(self.db_path) as conn:
            gw = ProgressGateway()
            service = SyncService(conn, gw, report=lambda _: None)
            service.shelf()
            # limit=0 fetches nothing
            self.assertEqual(service.progress(limit=0), 0)
            self.assertEqual(progress_calls, [])
            # limit=2 fetches the 2 books with highest read_update_time descending (b-fin=300, b-read=200), never albums
            self.assertEqual(service.progress(limit=2), 2)
            self.assertEqual(progress_calls, ["b-fin", "b-read"])
            # Next run only fetches the remaining unsynced book (b-unr) since b-fin and b-read are up-to-date
            progress_calls.clear()
            self.assertEqual(service.progress(limit=2), 1)
            self.assertEqual(progress_calls, ["b-unr"])
            # Check stored values and book_status view classification
            statuses = {
                r["book_id"]: dict(r)
                for r in conn.execute("SELECT * FROM book_status").fetchall()
            }
            self.assertEqual(statuses["b-fin"]["status"], "已读")
            self.assertEqual(statuses["b-fin"]["progress"], 100)
            self.assertEqual(statuses["b-fin"]["reading_seconds"], 7200)
            self.assertEqual(statuses["b-fin"]["finish_time"], 1700000000)
            self.assertEqual(statuses["b-read"]["status"], "在读")
            self.assertEqual(statuses["b-read"]["progress"], 35)
            self.assertEqual(statuses["b-unr"]["status"], "未读")

    def test_shelf_sync_counts_albums_and_mp_without_storing_albums_in_books(self):
        messages: list[str] = []

        class AlbumShelfGateway(FakeGateway):
            def call(self, endpoint, **params):
                if endpoint == "/shelf/sync":
                    return {
                        "books": [
                            {"bookId": "book-1", "title": "电子书1", "author": "A"},
                            {"bookId": "book-2", "title": "电子书2", "author": "B"},
                        ],
                        "albums": [
                            {"albumInfo": {"albumId": "alb-1", "name": "有声书1"}},
                            {"albumInfo": {"albumId": "alb-2", "name": "有声书2"}},
                            {"albumInfo": {"albumId": "alb-3", "name": "有声书3"}},
                        ],
                        "mp": {"book": {"bookId": "MP_WXS_1"}},
                    }
                return super().call(endpoint, **params)

        with connect(self.db_path) as conn:
            service = SyncService(conn, AlbumShelfGateway(), report=messages.append)
            total = service.shelf()
            # 2 ebooks + 3 albums + 1 mp = 6
            self.assertEqual(total, 6)
            self.assertTrue(any("书架：6 本（电子书 2，有声书 3，文章收藏 1）" in m for m in messages))
            # Albums are not stored in the books table
            book_ids = {r[0] for r in conn.execute("SELECT book_id FROM books").fetchall()}
            self.assertEqual(book_ids, {"book-1", "book-2"})
