from __future__ import annotations

import random
import sqlite3
import time
from pathlib import Path
from typing import Any

INTERVAL_SCHEDULE = (1, 3, 7, 14, 30, 60, 120, 180)


def _interval_for_shown_count(shown_count: int) -> int:
    idx = max(0, min(shown_count - 1, len(INTERVAL_SCHEDULE) - 1))
    return INTERVAL_SCHEDULE[idx]


def _ensure_review_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS review_log (
          item_type TEXT NOT NULL,
          item_id TEXT NOT NULL,
          shown_count INTEGER NOT NULL DEFAULT 0,
          interval_days INTEGER NOT NULL DEFAULT 0,
          last_shown INTEGER NOT NULL DEFAULT 0,
          due_at INTEGER NOT NULL DEFAULT 0,
          PRIMARY KEY (item_type, item_id)
        )"""
    )


def select_review_items(
    conn: sqlite3.Connection,
    n: int = 5,
    *,
    book: str | None = None,
    seed: int | None = None,
    dry_run: bool = False,
    now: int | None = None,
) -> list[dict[str, Any]]:
    _ensure_review_table(conn)
    if n <= 0:
        return []
    now_ts = int(now if now is not None else time.time())

    book_filter_sql = ""
    book_params: tuple[str, ...] = ()
    if book:
        kw = book.strip()
        book_filter_sql = " AND (b.title LIKE ? OR b.book_id = ?)"
        book_params = (f"%{kw}%", kw)

    hl_rows = conn.execute(
        f"""SELECT
          'highlight' AS item_type,
          h.bookmark_id AS item_id,
          h.book_id AS book_id,
          b.title AS book_title,
          b.reader_link AS reader_link,
          h.chapter_title AS chapter_title,
          h.page AS page,
          h.mark_text AS text,
          NULL AS thought_text,
          r.shown_count AS shown_count,
          r.interval_days AS interval_days,
          r.last_shown AS last_shown,
          r.due_at AS due_at
        FROM highlights h
        JOIN books b ON b.book_id = h.book_id
        LEFT JOIN review_log r ON r.item_type = 'highlight' AND r.item_id = h.bookmark_id
        WHERE COALESCE(h.mark_text, '') != ''{book_filter_sql}
        ORDER BY h.bookmark_id""",
        book_params,
    ).fetchall()

    th_rows = conn.execute(
        f"""SELECT
          'thought' AS item_type,
          t.review_id AS item_id,
          t.book_id AS book_id,
          b.title AS book_title,
          b.reader_link AS reader_link,
          t.chapter_name AS chapter_title,
          t.page AS page,
          t.abstract AS text,
          t.content AS thought_text,
          r.shown_count AS shown_count,
          r.interval_days AS interval_days,
          r.last_shown AS last_shown,
          r.due_at AS due_at
        FROM thoughts t
        JOIN books b ON b.book_id = t.book_id
        LEFT JOIN review_log r ON r.item_type = 'thought' AND r.item_id = t.review_id
        WHERE COALESCE(t.content, '') != ''{book_filter_sql}
        ORDER BY t.review_id""",
        book_params,
    ).fetchall()

    due_items: list[dict[str, Any]] = []
    unshown_items: list[dict[str, Any]] = []

    for row in [*hl_rows, *th_rows]:
        item = dict(row)
        shown_count = item["shown_count"]
        due_at = item["due_at"]
        if shown_count is None or int(shown_count) == 0:
            if due_at is not None and int(due_at) > 0 and int(due_at) <= now_ts:
                due_items.append(item)
            else:
                unshown_items.append(item)
        elif int(due_at or 0) <= now_ts:
            due_items.append(item)
        # else: due_at > now_ts (already reviewed and not yet due), skip

    due_items.sort(key=lambda x: (int(x["due_at"] or 0), str(x["item_type"]), str(x["item_id"])))
    unshown_items.sort(key=lambda x: (str(x["item_type"]), str(x["item_id"])))

    rng = random.Random(seed)
    rng.shuffle(unshown_items)

    selected = due_items[:n]
    if len(selected) < n:
        selected.extend(unshown_items[: n - len(selected)])

    if not dry_run and selected:
        with conn:
            for item in selected:
                new_shown = int(item["shown_count"] or 0) + 1
                interval_days = _interval_for_shown_count(new_shown)
                new_due_at = now_ts + interval_days * 86400
                updated = conn.execute(
                    """UPDATE review_log SET
                      shown_count=?, interval_days=?, last_shown=?, due_at=?
                    WHERE item_type=? AND item_id=?""",
                    (new_shown, interval_days, now_ts, new_due_at, item["item_type"], item["item_id"]),
                )
                if updated.rowcount == 0:
                    conn.execute(
                        """INSERT INTO review_log(
                          item_type, item_id, shown_count, interval_days, last_shown, due_at
                        ) VALUES (?, ?, ?, ?, ?, ?)""",
                        (item["item_type"], item["item_id"], new_shown, interval_days, now_ts, new_due_at),
                    )
                item["shown_count"] = new_shown
                item["interval_days"] = interval_days
                item["last_shown"] = now_ts
                item["due_at"] = new_due_at

    return selected


def format_review_markdown(items: list[dict[str, Any]], now: int | None = None) -> str:
    now_ts = int(now if now is not None else time.time())
    date_str = time.strftime("%Y-%m-%d", time.localtime(now_ts))
    lines = [f"## 每日回顾 {date_str}", ""]
    if not items:
        lines.append("暂无可回顾的笔记。")
        return "\n".join(lines)

    for item in items:
        if item["item_type"] == "highlight":
            for qline in str(item["text"] or "").splitlines() or [""]:
                lines.append(f"> {qline}")
        else:
            if item.get("text"):
                for qline in str(item["text"]).splitlines():
                    lines.append(f"> {qline}")
                lines.append(f"💭 {item.get('thought_text') or ''}")
            else:
                thought_val = str(item.get("thought_text") or "")
                for qline in thought_val.splitlines() or [""]:
                    lines.append(f"> {qline}")
                lines.append(f"💭 {thought_val}")

        loc = item.get("chapter_title") or (f"p.{item['page']}" if item.get("page") else "") or ""
        loc_part = f" {loc}" if loc else ""
        link_part = f" [打开阅读]({item['reader_link']})" if item.get("reader_link") else ""
        book_title = item.get("book_title") or item.get("book_id") or "未命名"
        lines.append(f"—— 《{book_title}》{loc_part}{link_part}")
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def run_review(
    conn: sqlite3.Connection,
    n: int = 5,
    *,
    append_path: Path | None = None,
    dry_run: bool = False,
    seed: int | None = None,
    book: str | None = None,
    now: int | None = None,
) -> str:
    items = select_review_items(conn, n=n, book=book, seed=seed, dry_run=dry_run, now=now)
    markdown = format_review_markdown(items, now=now)
    if append_path is not None:
        append_path.parent.mkdir(parents=True, exist_ok=True)
        if append_path.exists():
            existing = append_path.read_text(encoding="utf-8")
            if existing and not existing.endswith("\n"):
                existing += "\n"
            prefix = f"{existing}\n" if existing else ""
            append_path.write_text(f"{prefix}{markdown}\n", encoding="utf-8")
        else:
            append_path.write_text(f"{markdown}\n", encoding="utf-8")
    return markdown
