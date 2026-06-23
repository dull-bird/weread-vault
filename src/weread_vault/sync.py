from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Callable
from typing import Any

from .db import set_state
from .gateway import Gateway

Reporter = Callable[[str], None]


class SyncService:
    def __init__(self, conn: sqlite3.Connection, gateway: Gateway, report: Reporter = print):
        self.conn = conn
        self.gateway = gateway
        self.report = report

    def _run(self, scope: str, action: Callable[[], int]) -> int:
        started = int(time.time())
        # A terminal/process can disappear mid-sync. Do not leave a misleading
        # permanent "running" state; committed books remain safe and retryable.
        self.conn.execute(
            """UPDATE sync_runs SET completed_at=?, status='interrupted',
            detail='检测到未完成的旧同步；新同步开始前已标记为中断'
            WHERE status='running'""",
            (started,),
        )
        run = self.conn.execute(
            "INSERT INTO sync_runs(started_at, status, scope) VALUES (?, 'running', ?)", (started, scope)
        )
        self.conn.commit()
        try:
            count = action()
        except BaseException as error:
            self.conn.execute(
                "UPDATE sync_runs SET completed_at=?, status='failed', detail=? WHERE id=?",
                (int(time.time()), str(error), run.lastrowid),
            )
            self.conn.commit()
            raise
        self.conn.execute(
            "UPDATE sync_runs SET completed_at=?, status='success', detail=? WHERE id=?",
            (int(time.time()), f"{count} 项", run.lastrowid),
        )
        set_state(self.conn, f"{scope}_synced_at", str(int(time.time())))
        self.conn.commit()
        return count

    def books(self) -> int:
        return self._run("books", self._sync_books)

    def notes(self, full: bool = False, limit: int | None = None) -> int:
        return self._run("notes", lambda: self._sync_notes(full, limit))

    def stats(self) -> int:
        return self._run("stats", self._sync_stats)

    def info(self, limit: int | None = None, refresh: bool = False) -> int:
        return self._run("info", lambda: self._sync_book_info(limit, refresh))

    def shelf(self) -> int:
        return self._run("shelf", self._sync_shelf)

    def all(self, full_notes: bool = False, note_limit: int | None = None) -> dict[str, int]:
        return {"shelf": self.shelf(), "books": self.books(),
                "notes": self.notes(full_notes, note_limit), "stats": self.stats()}

    def _sync_shelf(self) -> int:
        # The whole bookshelf, including books without any notes. Non-destructive: never
        # overwrites note counts / sort / progress that the notebooks sync owns for noted books.
        payload = self.gateway.call("/shelf/sync")
        books = payload.get("books") or []
        now = int(time.time())
        with self.conn:
            for item in books:
                self._upsert_shelf_book(item, now)
        self.report(f"书架：{len(books)} 本")
        return len(books)

    def _upsert_shelf_book(self, item: dict[str, Any], now: int) -> None:
        book_id = item.get("bookId")
        if not book_id:
            return
        category = item.get("category")
        if isinstance(category, list):
            category = (category[0] or {}).get("title") if category else None
        elif not isinstance(category, str):
            category = None
        finished = item.get("finishReading")
        updated = self.conn.execute(
            """UPDATE books SET title=COALESCE(?,title), author=COALESCE(?,author),
            cover=COALESCE(?,cover), category=COALESCE(category,?), finished=COALESCE(?,finished)
            WHERE book_id=?""",
            (item.get("title"), item.get("author"), item.get("cover"), category, finished, str(book_id)),
        )
        if updated.rowcount == 0:
            self.conn.execute(
                """INSERT INTO books(book_id,title,author,cover,category,finished,total_notes,sort,synced_at)
                VALUES (?,?,?,?,?,?,0,?,?)""",
                (str(book_id), item.get("title"), item.get("author"), item.get("cover"), category, finished,
                 item.get("updateTime") or now, now),
            )

    def _sync_book_info(self, limit: int | None, refresh: bool = False) -> int:
        # Backfill rich metadata only for books not yet enriched (rating IS NULL), so this is
        # incremental: a one-time pass after upgrade, then effectively free on later runs.
        # refresh=True re-fetches every book (e.g. to backfill a newly added field like intro).
        where = "" if refresh else "WHERE rating IS NULL"
        sql = f"SELECT book_id, title FROM books {where} ORDER BY sort DESC"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        rows = self.conn.execute(sql).fetchall()
        total = len(rows)
        self.report(f"书籍信息：待补全 {total} 本")
        done = 0
        for index, book in enumerate(rows, 1):
            try:
                info = self.gateway.call("/book/info", bookId=book["book_id"])
                with self.conn:
                    self.conn.execute(
                        """UPDATE books SET rating=?, rating_count=?, word_count=?, publisher=?, isbn=?,
                        translator=?, intro=COALESCE(NULLIF(?,''), intro) WHERE book_id=?""",
                        (int(info.get("newRating") or 0), info.get("newRatingCount"), info.get("wordCount"),
                         info.get("publisher"), info.get("isbn"), info.get("translator"),
                         info.get("intro"), book["book_id"]),
                    )
                done += 1
                self.report(f"书籍信息：[{index}/{total}] {book['title'] or book['book_id']}")
            except Exception as error:
                self.report(f"书籍信息：[{index}/{total}] {book['title'] or book['book_id']} 失败：{error}")
            time.sleep(self.gateway.sleep_seconds)
        return done

    def _sync_books(self) -> int:
        last_sort: int | None = None
        count = 0
        while True:
            params: dict[str, Any] = {"count": 100}
            if last_sort is not None:
                params["lastSort"] = last_sort
            payload = self.gateway.call("/user/notebooks", **params)
            books = payload.get("books") or []
            if not books:
                break
            now = int(time.time())
            with self.conn:
                for item in books:
                    self._upsert_book(item, now)
            count += len(books)
            self.report(f"书目：已处理 {count} 本")
            if payload.get("hasMore") != 1:
                break
            next_sort = books[-1].get("sort")
            if next_sort is None or next_sort == last_sort:
                raise RuntimeError("书目分页游标没有前进，已停止以避免重复同步。")
            last_sort = next_sort
            time.sleep(self.gateway.sleep_seconds)
        return count

    def _upsert_book(self, item: dict[str, Any], now: int) -> None:
        info = item.get("book") or {}
        book_id = item.get("bookId")
        if not book_id:
            raise RuntimeError("书目响应缺少 bookId")
        categories = info.get("categories") or []
        category = (categories[0] or {}).get("title") if categories else None
        review_count = int(item.get("reviewCount") or 0)
        note_count = int(item.get("noteCount") or 0)
        bookmark_count = int(item.get("bookmarkCount") or 0)
        values = (
            info.get("title"), info.get("author"), info.get("cover"), info.get("intro"), category,
            info.get("publishTime"), review_count, note_count, bookmark_count,
            review_count + note_count + bookmark_count, item.get("readingProgress"), item.get("markedStatus"),
            info.get("finished"), item.get("sort"), now, str(book_id),
        )
        updated = self.conn.execute(
            """UPDATE books SET title=?,author=?,cover=?,intro=?,category=?,publish_time=?,review_count=?,
            note_count=?,bookmark_count=?,total_notes=?,reading_progress=?,marked_status=?,finished=?,sort=?,synced_at=?
            WHERE book_id=?""",
            values,
        )
        if updated.rowcount == 0:
            self.conn.execute(
                """INSERT INTO books(
                    title,author,cover,intro,category,publish_time,review_count,note_count,bookmark_count,
                    total_notes,reading_progress,marked_status,finished,sort,synced_at,book_id
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                values,
            )

    def _sync_notes(self, full: bool, limit: int | None) -> int:
        where = "" if full else "WHERE notes_synced_sort IS NULL OR sort > notes_synced_sort"
        sql = f"SELECT book_id, title, sort FROM books {where} ORDER BY sort DESC"  # controlled SQL fragment
        values: tuple[int, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            values = (limit,)
        rows = self.conn.execute(sql, values).fetchall()
        total = len(rows)
        self.report(f"笔记：待同步 {total} 本")
        synced = 0
        for index, book in enumerate(rows, 1):
            try:
                highlights = self._fetch_highlights(book["book_id"])
                thoughts = self._fetch_thoughts(book["book_id"])
                # All remote pages are collected before entering the transaction. A request failure
                # therefore cannot leave a partially refreshed book or advance its watermark.
                with self.conn:
                    self._replace_book_notes(book["book_id"], book["sort"], highlights, thoughts)
                synced += 1
                self.report(
                    f"笔记：[{index}/{total}] {book['title'] or book['book_id']} — "
                    f"划线 {len(highlights['updated'])}，想法 {len(thoughts)}"
                )
            except Exception as error:
                self.report(f"笔记：[{index}/{total}] {book['title'] or book['book_id']} 失败：{error}")
            time.sleep(self.gateway.sleep_seconds)
        if synced != total:
            raise RuntimeError(f"{total - synced} 本书同步失败；成功的书已安全提交，失败的书下次会重试。")
        return synced

    def _fetch_highlights(self, book_id: str) -> dict[str, Any]:
        payload = self.gateway.call("/book/bookmarklist", bookId=book_id)
        return {
            "chapters": payload.get("chapters") or [],
            "updated": payload.get("updated") or [],
            "removed": payload.get("removed") or [],
        }

    def _fetch_thoughts(self, book_id: str) -> list[dict[str, Any]]:
        reviews: list[dict[str, Any]] = []
        sync_key: int | str = 0
        seen_cursors: set[str] = set()
        while True:
            payload = self.gateway.call("/review/list/mine", bookid=book_id, count=50, synckey=sync_key)
            reviews.extend(payload.get("reviews") or [])
            if payload.get("hasMore") != 1:
                return reviews
            next_key = payload.get("synckey")
            if next_key is None or str(next_key) in seen_cursors:
                raise RuntimeError("想法分页游标没有前进，已停止以保护本地数据。")
            seen_cursors.add(str(next_key))
            sync_key = next_key
            time.sleep(self.gateway.sleep_seconds)

    def _replace_book_notes(
        self,
        book_id: str,
        book_sort: int | None,
        highlights: dict[str, Any],
        thoughts: list[dict[str, Any]],
    ) -> None:
        now = int(time.time())
        chapter_names = {chapter.get("chapterUid"): chapter.get("title") for chapter in highlights["chapters"]}
        for removed in highlights["removed"]:
            bookmark_id = removed if isinstance(removed, str) else (removed or {}).get("bookmarkId")
            if bookmark_id:
                self.conn.execute("DELETE FROM highlights WHERE bookmark_id=?", (str(bookmark_id),))
        for item in highlights["updated"]:
            bookmark_id = item.get("bookmarkId")
            if not bookmark_id:
                continue
            chapter_uid = item.get("chapterUid")
            values = (book_id, chapter_uid, chapter_names.get(chapter_uid), item.get("markText"), item.get("range"),
                      item.get("colorStyle"), item.get("createTime"), now, str(bookmark_id))
            updated = self.conn.execute(
                """UPDATE highlights SET book_id=?,chapter_uid=?,chapter_title=?,mark_text=?,text_range=?,
                color_style=?,create_time=?,updated_at=? WHERE bookmark_id=?""", values
            )
            if updated.rowcount == 0:
                self.conn.execute(
                    """INSERT INTO highlights(book_id,chapter_uid,chapter_title,mark_text,text_range,color_style,
                    create_time,updated_at,bookmark_id) VALUES (?,?,?,?,?,?,?,?,?)""", values
                )
        fetched_review_ids: list[str] = []
        for wrapper in thoughts:
            review = wrapper.get("review") or {}
            review_id = review.get("reviewId")
            if not review_id:
                continue
            review_id = str(review_id)
            fetched_review_ids.append(review_id)
            is_book_review = int(review.get("chapterName") is None and review.get("range") is None)
            values = (book_id, review.get("chapterUid"), review.get("chapterName"), review.get("content"),
                      review.get("star"), review.get("range"), is_book_review, review.get("createTime"), now, review_id)
            updated = self.conn.execute(
                """UPDATE thoughts SET book_id=?,chapter_uid=?,chapter_name=?,content=?,star=?,text_range=?,
                is_book_review=?,create_time=?,updated_at=? WHERE review_id=?""", values
            )
            if updated.rowcount == 0:
                self.conn.execute(
                    """INSERT INTO thoughts(book_id,chapter_uid,chapter_name,content,star,text_range,is_book_review,
                    create_time,updated_at,review_id) VALUES (?,?,?,?,?,?,?,?,?,?)""", values
                )
        # review/list/mine is fully paged above. Deleting only after all pages succeed keeps
        # local rows intact on network/API interruption and makes remote deletions visible.
        if fetched_review_ids:
            marks = ",".join("?" for _ in fetched_review_ids)
            self.conn.execute(
                f"DELETE FROM thoughts WHERE book_id=? AND review_id NOT IN ({marks})",  # values are bound
                [book_id, *fetched_review_ids],
            )
        else:
            self.conn.execute("DELETE FROM thoughts WHERE book_id=?", (book_id,))
        self.conn.execute("UPDATE books SET notes_synced_sort=? WHERE book_id=?", (book_sort, book_id))

    def _sync_stats(self) -> int:
        count = 0
        for mode in ("weekly", "monthly", "annually", "overall"):
            payload = self.gateway.call("/readdata/detail", mode=mode, baseTime=0)
            with self.conn:
                self.conn.execute(
                    "INSERT INTO reading_stats(mode, base_time, payload, fetched_at) VALUES (?, 0, ?, ?)",
                    (mode, json.dumps(payload, ensure_ascii=False, separators=(",", ":")), int(time.time())),
                )
            count += 1
            self.report(f"统计：{mode} 完成")
            time.sleep(self.gateway.sleep_seconds)
        return count
