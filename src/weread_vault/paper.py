from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from typing import Any

from .errors import WereadVaultError


def paper_book_id(title: str | None, author: str | None) -> str:
    norm_title = re.sub(r"\s+", " ", (title or "").strip()).lower()
    norm_author = re.sub(r"\s+", " ", (author or "").strip()).lower()
    digest = hashlib.sha1(f"{norm_title}|{norm_author}".encode("utf-8")).hexdigest()[:12]
    return f"PAPER_{digest}"


def paper_bookmark_id(book_id: str, page: str | None, highlight_text: str) -> str:
    digest = hashlib.sha1(
        f"{book_id}|{page or ''}|{highlight_text}".encode("utf-8")
    ).hexdigest()[:16]
    return f"paper:{digest}"


def paper_review_id(book_id: str, page: str | None, thought_text: str, highlight_text: str | None = None) -> str:
    payload = f"{book_id}|{page or ''}|{thought_text}"
    if highlight_text:
        payload += f"|{highlight_text}"
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
    return f"paper:{digest}"


def _parse_page_line(line: str) -> str | None:
    cleaned = line.strip().strip("[]()（）【】")
    if not cleaned:
        return None
    m = re.match(r"^[pP]{1,2}\.?\s*(\d+(?:\s*[-–~]\s*\d+)?)\s*$", cleaned)
    if m:
        return re.sub(r"\s+", "", m.group(1))
    m = re.match(r"^第\s*(\d+(?:\s*[-–~]\s*\d+)?)\s*页\s*$", cleaned)
    if m:
        return re.sub(r"\s+", "", m.group(1))
    m = re.match(r"^(?:页码|page)\s*[:：]?\s*[pP]?\.?\s*(\d+(?:\s*[-–~]\s*\d+)?)\s*$", cleaned, re.IGNORECASE)
    if m:
        return re.sub(r"\s+", "", m.group(1))
    return None


def _parse_note_block(block: str, book_id: str) -> dict[str, Any] | None:
    lines = block.splitlines()
    page: str | None = None
    highlight_lines: list[str] = []
    thought_lines: list[str] = []
    in_thought = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if not highlight_lines and not thought_lines and page is None:
            parsed_page = _parse_page_line(line)
            if parsed_page is not None:
                page = parsed_page
                continue
        if line.startswith(">"):
            in_thought = False
            hl_text = re.sub(r"^>\s?", "", line)
            highlight_lines.append(hl_text)
            continue
        thought_match = re.match(r"^(?:想法\s*[:：]|💭\s*[:：]?)\s*(.*)$", line)
        if thought_match:
            in_thought = True
            first_part = thought_match.group(1).strip()
            if first_part:
                thought_lines.append(first_part)
            continue
        if in_thought:
            thought_lines.append(line)

    highlight_text = "\n".join(highlight_lines).strip() or None
    thought_text = "\n".join(thought_lines).strip() or None
    if not highlight_text and not thought_text:
        return None

    note: dict[str, Any] = {
        "page": page,
        "highlight": highlight_text,
        "thought": thought_text,
        "bookmark_id": paper_bookmark_id(book_id, page, highlight_text) if highlight_text else None,
        "review_id": paper_review_id(book_id, page, thought_text, highlight_text) if thought_text else None,
    }
    return note


def parse_paper_notes(text: str) -> list[dict[str, Any]]:
    """解析纸质书笔记文本（可含多本书，每本以 `书名:` / `书名：` 开头）。"""
    raw_books: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        title_match = re.match(r"^(?:#+\s*)?书名\s*[:：]\s*(.+)$", stripped)
        if title_match:
            current = {
                "title": title_match.group(1).strip(),
                "author": "",
                "isbn": "",
                "publisher": "",
                "category": "",
                "_in_headers": True,
                "_body_lines": [],
            }
            raw_books.append(current)
            continue

        if current is None:
            continue

        if current["_in_headers"]:
            if not stripped:
                continue
            author_match = re.match(r"^(?:[-*]\s*)?作者\s*[:：]\s*(.*)$", stripped)
            if author_match:
                current["author"] = author_match.group(1).strip()
                continue
            isbn_match = re.match(r"^(?:[-*]\s*)?isbn\s*[:：]\s*(.*)$", stripped, re.IGNORECASE)
            if isbn_match:
                isbn_val = re.sub(r"\(.*?\)|（.*?）", "", isbn_match.group(1)).strip()
                current["isbn"] = isbn_val
                continue
            pub_match = re.match(r"^(?:[-*]\s*)?出版社\s*[:：]\s*(.*)$", stripped)
            if pub_match:
                current["publisher"] = pub_match.group(1).strip()
                continue
            cat_match = re.match(r"^(?:[-*]\s*)?分类\s*[:：]\s*(.*)$", stripped)
            if cat_match:
                current["category"] = cat_match.group(1).strip()
                continue
            current["_in_headers"] = False

        current["_body_lines"].append(raw_line)

    parsed: list[dict[str, Any]] = []
    for raw in raw_books:
        title = raw["title"]
        author = raw["author"]
        book_id = paper_book_id(title, author)
        body = "\n".join(raw["_body_lines"]).strip()
        blocks = re.split(r"\n\s*\n", body) if body else []
        notes: list[dict[str, Any]] = []
        for block in blocks:
            note = _parse_note_block(block, book_id)
            if note is not None:
                notes.append(note)
        parsed.append(
            {
                "book_id": book_id,
                "title": title,
                "author": author,
                "isbn": raw["isbn"],
                "publisher": raw["publisher"],
                "category": raw["category"],
                "notes": notes,
            }
        )

    if not parsed:
        raise WereadVaultError("未解析到任何纸质书（请以 `书名: ...` 开始每本书）。")
    return parsed


def format_dry_run(parsed_books: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    total_hl = 0
    total_th = 0
    for book in parsed_books:
        notes = book["notes"]
        hl_count = sum(1 for n in notes if n.get("highlight"))
        th_count = sum(1 for n in notes if n.get("thought"))
        total_hl += hl_count
        total_th += th_count
        header = f"《{book['title']}》"
        if book.get("author"):
            header += f" · 作者：{book['author']}"
        if book.get("isbn"):
            header += f" · ISBN：{book['isbn']}"
        header += f" · id={book['book_id']}（划线 {hl_count}，想法 {th_count}）"
        lines.append(header)
        for note in notes:
            page_str = f"[p.{note['page']}] " if note.get("page") else ""
            if note.get("highlight"):
                lines.append(f"  {page_str}> {note['highlight']}")
            if note.get("thought"):
                lines.append(f"  {page_str}💭 {note['thought']}")
    lines.append(f"共解析 {len(parsed_books)} 本纸质书，划线 {total_hl} 条，想法 {total_th} 条（dry-run 未写入数据库）。")
    return "\n".join(lines)


def import_paper_books(conn: sqlite3.Connection, parsed_books: list[dict[str, Any]]) -> dict[str, int]:
    now = int(time.time())
    imported_books = 0
    imported_highlights = 0
    imported_thoughts = 0

    with conn:
        for book in parsed_books:
            book_id = book["book_id"]
            title = book["title"]
            author = book["author"] or None
            isbn = book.get("isbn") or None
            publisher = book.get("publisher") or None
            category = book.get("category") or None

            updated = conn.execute(
                """UPDATE books SET
                  title=COALESCE(NULLIF(?,''), title),
                  author=COALESCE(NULLIF(?,''), author),
                  isbn=COALESCE(NULLIF(?,''), isbn),
                  publisher=COALESCE(NULLIF(?,''), publisher),
                  category=COALESCE(NULLIF(?,''), category),
                  source='paper',
                  synced_at=?
                WHERE book_id=?""",
                (title, author or "", isbn or "", publisher or "", category or "", now, book_id),
            )
            if updated.rowcount == 0:
                conn.execute(
                    """INSERT INTO books(
                      book_id, title, author, isbn, publisher, category,
                      source, on_shelf, review_count, note_count, bookmark_count,
                      total_notes, sort, synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'paper', 1, 0, 0, 0, 0, ?, ?)""",
                    (book_id, title, author, isbn, publisher, category, now, now),
                )

            for note in book["notes"]:
                page = note.get("page")
                chapter_label = f"p.{page}" if page else None
                num_match = re.match(r"^\d+", page) if page else None
                chapter_uid = int(num_match.group(0)) if num_match else None

                if note.get("highlight"):
                    bm_id = note["bookmark_id"]
                    hl_text = note["highlight"]
                    u_hl = conn.execute(
                        """UPDATE highlights SET
                          book_id=?, chapter_uid=?, chapter_title=?, mark_text=?,
                          source='paper', page=?, updated_at=?
                        WHERE bookmark_id=?""",
                        (book_id, chapter_uid, chapter_label, hl_text, page, now, bm_id),
                    )
                    if u_hl.rowcount == 0:
                        conn.execute(
                            """INSERT INTO highlights(
                              bookmark_id, book_id, chapter_uid, chapter_title, mark_text,
                              text_range, source, page, create_time, updated_at
                            ) VALUES (?, ?, ?, ?, ?, NULL, 'paper', ?, ?, ?)""",
                            (bm_id, book_id, chapter_uid, chapter_label, hl_text, page, now, now),
                        )
                    imported_highlights += 1

                if note.get("thought"):
                    rv_id = note["review_id"]
                    th_text = note["thought"]
                    abs_text = note.get("highlight") or None
                    u_th = conn.execute(
                        """UPDATE thoughts SET
                          book_id=?, chapter_uid=?, chapter_name=?, content=?, abstract=?,
                          source='paper', page=?, is_book_review=0, updated_at=?
                        WHERE review_id=?""",
                        (book_id, chapter_uid, chapter_label, th_text, abs_text, page, now, rv_id),
                    )
                    if u_th.rowcount == 0:
                        conn.execute(
                            """INSERT INTO thoughts(
                              review_id, book_id, chapter_uid, chapter_name, content, abstract,
                              text_range, is_book_review, source, page, create_time, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, NULL, 0, 'paper', ?, ?, ?)""",
                            (rv_id, book_id, chapter_uid, chapter_label, th_text, abs_text, page, now, now),
                        )
                    imported_thoughts += 1

            bm_count = int(
                conn.execute("SELECT count(*) FROM highlights WHERE book_id=?", (book_id,)).fetchone()[0] or 0
            )
            rv_count = int(
                conn.execute("SELECT count(*) FROM thoughts WHERE book_id=?", (book_id,)).fetchone()[0] or 0
            )
            total_notes = bm_count + rv_count
            conn.execute(
                """UPDATE books SET
                  bookmark_count=?, review_count=?, total_notes=?, sort=COALESCE(sort, ?), source='paper'
                WHERE book_id=?""",
                (bm_count, rv_count, total_notes, now, book_id),
            )
            imported_books += 1

    return {
        "books": imported_books,
        "highlights": imported_highlights,
        "thoughts": imported_thoughts,
    }
