from __future__ import annotations

import re
import sqlite3
import time
from pathlib import Path


def _safe_name(value: str | None) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", value or "未命名").strip()
    return name[:80] or "未命名"


def _date(value: int | None) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(value)) if value else ""


def export_markdown(conn: sqlite3.Connection, destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    books = conn.execute("SELECT * FROM books WHERE total_notes > 0 ORDER BY sort DESC").fetchall()
    names: dict[str, str] = {}
    exported = 0
    for book in books:
        highlights = conn.execute(
            "SELECT * FROM highlights WHERE book_id=? ORDER BY chapter_uid, text_range", (book["book_id"],)
        ).fetchall()
        thoughts = conn.execute(
            "SELECT * FROM thoughts WHERE book_id=? ORDER BY is_book_review DESC, chapter_uid", (book["book_id"],)
        ).fetchall()
        if not highlights and not thoughts:
            continue
        filename = _safe_name(book["title"])
        if filename in names and names[filename] != book["book_id"]:
            filename = f"{filename}-{book['book_id']}"
        names[filename] = book["book_id"]
        progress = book["reading_progress"] or 0
        lines = [
            "---",
            f'title: "{(book["title"] or "").replace(chr(34), "")}"',
            f'author: "{book["author"] or ""}"',
            f'book_id: "{book["book_id"]}"',
            "source: " + '"微信读书"',
            f"progress: {progress}",
            f"highlights: {len(highlights)}",
            f"thoughts: {len(thoughts)}",
            "---",
            "",
            f"# {book['title'] or '未命名'}",
            "",
            f"> 作者：{book['author'] or '未知'} · 进度：{progress}%",
            "",
            f"[在微信读书中打开](weread://reading?bId={book['book_id']})",
            "",
        ]
        book_reviews = [item for item in thoughts if item["is_book_review"]]
        if book_reviews:
            lines.extend(["## 我的书评", ""])
            for item in book_reviews:
                lines.extend([item["content"] or "", "", f"<small>{_date(item['create_time'])}</small>", ""])
        if highlights:
            lines.extend(["## 划线", ""])
            current_chapter = object()
            for item in highlights:
                if item["chapter_uid"] != current_chapter:
                    current_chapter = item["chapter_uid"]
                    if item["chapter_title"]:
                        lines.extend([f"### {item['chapter_title']}", ""])
                lines.extend([f"- {item['mark_text'] or ''}", ""])
        chapter_thoughts = [item for item in thoughts if not item["is_book_review"]]
        if chapter_thoughts:
            lines.extend(["## 我的想法", ""])
            for item in chapter_thoughts:
                prefix = f"【{item['chapter_name']}】" if item["chapter_name"] else ""
                lines.extend([f"- {prefix}{item['content'] or ''}", f"  <small>{_date(item['create_time'])}</small>", ""])
        (destination / f"{filename}.md").write_text("\n".join(lines), encoding="utf-8")
        exported += 1
    return exported
