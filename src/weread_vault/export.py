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


# 脚本管理的 frontmatter 字段（每次从微信读书真相刷新）；其余字段视为用户在
# Obsidian 里自加（分类/评分/重读标记等），重新导出时予以保留。
_MANAGED_FRONTMATTER = {"title", "author", "book_id", "source", "category", "cover", "progress", "highlights", "thoughts"}


def _user_frontmatter(path: Path) -> list[str]:
    """返回已有文件中用户自加的 frontmatter 行（脚本管理字段除外）。"""
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    if not text.startswith("---"):
        return []
    parts = text.split("---", 2)
    if len(parts) < 3:
        return []
    preserved: list[str] = []
    keep = False
    for line in parts[1].strip("\n").splitlines():
        # 顶层 key 行：非空格开头且含冒号；其续行（缩进的列表等）跟随上一个 key 的去留
        if line and not line[0].isspace() and ":" in line:
            keep = line.split(":", 1)[0].strip() not in _MANAGED_FRONTMATTER
        if keep:
            preserved.append(line)
    return preserved


def export_markdown(conn: sqlite3.Connection, destination: Path, force: bool = False) -> int:
    """渲染每本有笔记的书为 markdown。返回本次实际写入（新建或有变化）的篇数。

    增量：渲染结果与磁盘内容一致时跳过写入，不改动 mtime，避免触发
    iCloud 重传 / Obsidian / 索引重建。``force=True`` 则忽略增量强制全量重写。
    用户在 frontmatter 中自加的字段会被保留。
    """
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
        path = destination / f"{filename}.md"
        progress = book["reading_progress"] or 0
        lines = [
            "---",
            f'title: "{(book["title"] or "").replace(chr(34), "")}"',
            f'author: "{book["author"] or ""}"',
            f'book_id: "{book["book_id"]}"',
            "source: " + '"微信读书"',
            f'category: "{book["category"] or ""}"',
            f'cover: "{book["cover"] or ""}"',
            f"progress: {progress}",
            f"highlights: {len(highlights)}",
            f"thoughts: {len(thoughts)}",
            *_user_frontmatter(path),
            "---",
            "",
            f"# {book['title'] or '未命名'}",
            "",
            *([f"![{(book['title'] or '封面').replace(chr(34), '')}]({book['cover']})", ""] if book["cover"] else []),
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
        content = "\n".join(lines)
        if not force and path.exists() and path.read_text(encoding="utf-8") == content:
            continue
        path.write_text(content, encoding="utf-8")
        exported += 1
    return exported
