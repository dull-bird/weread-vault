"""Push archived WeRead notes to external knowledge tools (flomo, Notion).

Each exporter takes an injectable ``poster`` so the network call can be stubbed in
tests. Secrets (flomo webhook, Notion token) are passed in by the caller and are
never logged. Exporters only read the local database and POST the user's own data
to the user's own destination.
"""

from __future__ import annotations

import json
import sqlite3
import urllib.request
from collections.abc import Callable
from typing import Any

from .errors import WereadVaultError

Poster = Callable[[str, dict[str, Any], dict[str, str]], dict[str, Any]]


def _http_post(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def _books_with_notes(conn: sqlite3.Connection, limit: int | None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM books WHERE total_notes > 0 ORDER BY sort DESC"
    if limit is not None:
        if limit < 1:
            raise WereadVaultError("--limit 必须是正整数。")
        sql += f" LIMIT {int(limit)}"
    return conn.execute(sql).fetchall()


def _notes(conn: sqlite3.Connection, book_id: str) -> tuple[list[sqlite3.Row], list[sqlite3.Row]]:
    highlights = conn.execute(
        "SELECT chapter_title, mark_text FROM highlights WHERE book_id=? ORDER BY chapter_uid, text_range",
        (book_id,),
    ).fetchall()
    thoughts = conn.execute(
        "SELECT chapter_name, content FROM thoughts WHERE book_id=? ORDER BY is_book_review DESC, chapter_uid",
        (book_id,),
    ).fetchall()
    return highlights, thoughts


def _flomo_memo(book: sqlite3.Row, highlights: list[sqlite3.Row], thoughts: list[sqlite3.Row]) -> str:
    lines = [f"《{book['title'] or '未命名'}》 {book['author'] or ''}".rstrip()]
    for highlight in highlights:
        text = (highlight["mark_text"] or "").strip()
        if text:
            lines.append(f"- {text}")
    for thought in thoughts:
        text = (thought["content"] or "").strip()
        if text:
            lines.append(f"💭 {text}")
    tags = ["#微信读书"]
    category = (book["category"] or "").split("-")[0].strip()
    if category:
        tags.append(f"#{category}")
    lines.append(" ".join(tags))
    return "\n".join(lines)


def export_flomo(conn: sqlite3.Connection, webhook: str, limit: int | None = None, poster: Poster = _http_post) -> int:
    """Send one flomo memo per book (title + highlights + thoughts + tags). Returns memos sent."""
    if not webhook:
        raise WereadVaultError("缺少 flomo webhook。")
    sent = 0
    for book in _books_with_notes(conn, limit):
        highlights, thoughts = _notes(conn, book["book_id"])
        if not highlights and not thoughts:
            continue
        poster(webhook, {"content": _flomo_memo(book, highlights, thoughts)}, {})
        sent += 1
    return sent


def _text_block(kind: str, text: str) -> dict[str, Any]:
    # Notion rich-text caps at 2000 chars per block; keep each note within that.
    return {
        "object": "block", "type": kind,
        kind: {"rich_text": [{"type": "text", "text": {"content": text[:1990]}}]},
    }


def _notion_blocks(highlights: list[sqlite3.Row], thoughts: list[sqlite3.Row]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current_chapter = None
    for highlight in highlights:
        chapter = highlight["chapter_title"]
        if chapter and chapter != current_chapter:
            current_chapter = chapter
            blocks.append(_text_block("heading_2", chapter))
        text = (highlight["mark_text"] or "").strip()
        if text:
            blocks.append(_text_block("quote", text))
    for thought in thoughts:
        text = (thought["content"] or "").strip()
        if text:
            blocks.append(_text_block("callout", text))
    return blocks[:100]  # Notion accepts at most 100 children per page-create call.


def export_notion(
    conn: sqlite3.Connection, token: str, database_id: str, limit: int | None = None, poster: Poster = _http_post
) -> int:
    """Create one Notion page per book under the given database. Returns pages created."""
    if not token or not database_id:
        raise WereadVaultError("缺少 Notion token 或 database id。")
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}
    created = 0
    for book in _books_with_notes(conn, limit):
        highlights, thoughts = _notes(conn, book["book_id"])
        if not highlights and not thoughts:
            continue
        payload = {
            "parent": {"database_id": database_id},
            "properties": {"Name": {"title": [{"text": {"content": (book["title"] or "未命名")[:1990]}}]}},
            "children": _notion_blocks(highlights, thoughts),
        }
        poster("https://api.notion.com/v1/pages", payload, headers)
        created += 1
    return created
