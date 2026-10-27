from __future__ import annotations

import re
import sqlite3
import time
from pathlib import Path


def _position(text_range: str | None, page: str | None = None) -> int:
    """Numeric sort position: range start for WeRead notes, page number for paper notes."""
    head = str(text_range or "").split("-")[0]
    if head.isdigit():
        return int(head)
    digits = "".join(ch for ch in str(page or "") if ch.isdigit())
    return int(digits) if digits else 0


def _safe_name(value: str | None) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", value or "未命名").strip()
    return name[:80] or "未命名"


def _date(value: int | None) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(value)) if value else ""


# 脚本管理的 frontmatter 字段（每次从微信读书真相刷新）；其余字段视为用户在
# Obsidian 里自加（分类/评分/重读标记等），重新导出时予以保留。
_MANAGED_FRONTMATTER = {"title", "author", "book_id", "source", "category", "cover", "progress", "highlights", "thoughts"}

_OBSIDIAN_MANAGED_FRONTMATTER = {
    "title", "author", "book_id", "source", "category", "cover",
    "isbn", "publisher", "rating", "progress", "status",
    "reading_hours", "finish_date", "highlights", "thoughts",
    "reader_link", "updated",
}

BEGIN_NOTES = "<!-- weread-vault:begin notes -->"
END_NOTES = "<!-- weread-vault:end notes -->"


class ObsidianExportResult(int):
    """Int subclass returning number of written files while exposing created/appended/new_items counts."""

    created: int
    appended: int
    new_items: int
    written: int

    def __new__(cls, written: int, *, created: int = 0, appended: int = 0, new_items: int = 0) -> ObsidianExportResult:
        obj = super().__new__(cls, written)
        obj.written = written
        obj.created = created
        obj.appended = appended
        obj.new_items = new_items
        return obj

    def __getitem__(self, key: str) -> int:
        return int(getattr(self, key))


def _user_frontmatter(path: Path, managed: set[str] = _MANAGED_FRONTMATTER) -> list[str]:
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
            keep = line.split(":", 1)[0].strip() not in managed
        if keep:
            preserved.append(line)
    return preserved


def _range_span(value: str | None) -> tuple[int, int] | None:
    if not value:
        return None
    parts = str(value).split("-")
    if not parts[0].lstrip("-").isdigit():
        return None
    start = int(parts[0])
    end = int(parts[1]) if len(parts) > 1 and parts[1].lstrip("-").isdigit() else start
    return (start, end)


def _merge_highlights(highlights: list, popular: list) -> dict:
    """Merge own and popular highlights per chapter, ordered by position. A popular highlight that
    overlaps an own one is folded into it (annotated with the reader count) instead of duplicated.
    Returns {chapter_uid: {"title": str, "entries": [ {own/text/count/pos} ... ordered ]}}."""
    chapters: dict = {}

    def bucket(chapter_uid, title):
        return chapters.setdefault(chapter_uid, {"title": title, "own": [], "pop": []})

    for h in highlights:
        span = _range_span(h["text_range"])
        bucket(h["chapter_uid"], h["chapter_title"])["own"].append(
            {"text": h["mark_text"] or "", "span": span, "pos": span[0] if span else 0, "count": 0,
             "text_range": h["text_range"], "chapter_uid": h["chapter_uid"]})
    for p in popular:
        span = _range_span(p["text_range"])
        bucket(p["chapter_uid"], p["chapter_title"])["pop"].append(
            {"text": p["mark_text"] or "", "span": span, "pos": span[0] if span else 0, "count": p["count"] or 0})

    result: dict = {}
    for chapter_uid, data in chapters.items():
        entries: list = []
        for own in data["own"]:
            for pop in data["pop"]:
                if own["span"] and pop["span"] and own["span"][0] <= pop["span"][1] and pop["span"][0] <= own["span"][1]:
                    own["count"] = max(own["count"], pop["count"])  # overlapping → fold count into own
                    pop["merged"] = True
            entries.append({"kind": "own", **own})
        for pop in data["pop"]:
            if not pop.get("merged"):
                entries.append({"kind": "pop", **pop})
        entries.sort(key=lambda item: item["pos"])
        result[chapter_uid] = {"title": data["title"], "entries": entries}
    return result


def export_markdown(conn: sqlite3.Connection, destination: Path, force: bool = False,
                    with_popular: bool = False) -> int:
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
        popular = conn.execute(
            "SELECT * FROM popular_highlights WHERE book_id=? ORDER BY chapter_uid, text_range", (book["book_id"],)
        ).fetchall() if with_popular else []
        if not highlights and not thoughts:
            continue
        filename = _safe_name(book["title"])
        if filename in names and names[filename] != book["book_id"]:
            filename = f"{filename}-{book['book_id']}"
        names[filename] = book["book_id"]
        path = destination / f"{filename}.md"
        progress = book["reading_progress"] or 0
        if book["reader_link"]:
            link_lines = [f"[打开阅读]({book['reader_link']})", ""]
        elif book["deep_link"]:
            link_lines = [f"[查看详情]({book['deep_link']})", ""]
        else:
            link_lines = []
        is_paper = ("source" in book.keys() and book["source"] == "paper") or str(book["book_id"]).startswith("PAPER_")
        source_label = "纸质书" if is_paper else "微信读书"
        lines = [
            "---",
            f'title: "{(book["title"] or "").replace(chr(34), "")}"',
            f'author: "{book["author"] or ""}"',
            f'book_id: "{book["book_id"]}"',
            f'source: "{source_label}"',
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
            *link_lines,
        ]
        book_reviews = [item for item in thoughts if item["is_book_review"] and not item["abstract"]]
        chapter_thoughts = [item for item in thoughts if not (item["is_book_review"] and not item["abstract"])]
        hl_keys: set[tuple[object, str]] = set()
        hl_ranges: set[str] = set()
        for h in highlights:
            if h["text_range"]:
                hl_keys.add((h["chapter_uid"], str(h["text_range"])))
                hl_ranges.add(str(h["text_range"]))
        attached_by_key: dict[tuple[object, str], list] = {}
        attached_by_range: dict[str, list] = {}
        remaining_thoughts: list = []
        for item in chapter_thoughts:
            tr = str(item["text_range"]) if item["text_range"] else ""
            if tr and (item["chapter_uid"], tr) in hl_keys:
                attached_by_key.setdefault((item["chapter_uid"], tr), []).append(item)
            elif tr and tr in hl_ranges:
                attached_by_range.setdefault(tr, []).append(item)
            else:
                remaining_thoughts.append(item)

        def _attached_for(chapter_uid: object, text_range: object) -> list:
            if not text_range:
                return []
            tr = str(text_range)
            return [*attached_by_key.get((chapter_uid, tr), []), *attached_by_range.get(tr, [])]

        if book_reviews:
            lines.extend(["## 我的书评", ""])
            for item in book_reviews:
                lines.extend([item["content"] or "", "", f"<small>{_date(item['create_time'])}</small>", ""])
        if with_popular and (highlights or popular):
            merged = _merge_highlights(list(highlights), list(popular))
            lines.extend(["## 划线（含他人热门）", ""])
            for chapter_uid, chapter in merged.items():
                if chapter["title"]:
                    lines.extend([f"### {chapter['title']}", ""])
                for entry in chapter["entries"]:
                    if entry["kind"] == "own":
                        suffix = f" <small>🔥 {entry['count']} 人也划</small>" if entry["count"] else ""
                        lines.append(f"- {entry['text']}{suffix}")
                        for th in _attached_for(entry.get("chapter_uid"), entry.get("text_range")):
                            lines.append(f"💭 {th['content'] or ''}")
                            if th["create_time"]:
                                lines.append(f"  <small>{_date(th['create_time'])}</small>")
                        lines.append("")
                    else:
                        lines.extend([f"- 🔥 {entry['text']} <small>（{entry['count']} 人划线）</small>", ""])
        elif highlights:
            lines.extend(["## 划线", ""])
            current_chapter = object()
            for item in highlights:
                if item["chapter_uid"] != current_chapter:
                    current_chapter = item["chapter_uid"]
                    if item["chapter_title"]:
                        lines.extend([f"### {item['chapter_title']}", ""])
                lines.append(f"- {item['mark_text'] or ''}")
                for th in _attached_for(item["chapter_uid"], item["text_range"]):
                    lines.append(f"💭 {th['content'] or ''}")
                    if th["create_time"]:
                        lines.append(f"  <small>{_date(th['create_time'])}</small>")
                lines.append("")
        if remaining_thoughts:
            lines.extend(["## 我的想法", ""])
            for item in remaining_thoughts:
                if item["abstract"]:
                    lines.extend([f"> {item['abstract']}", f"💭 {item['content'] or ''}",
                                  f"<small>{_date(item['create_time'])}</small>", ""])
                else:
                    prefix = f"【{item['chapter_name']}】" if item["chapter_name"] else ""
                    lines.extend([f"- {prefix}{item['content'] or ''}", f"  <small>{_date(item['create_time'])}</small>", ""])
        content = "\n".join(lines)
        if not force and path.exists() and path.read_text(encoding="utf-8") == content:
            continue
        path.write_text(content, encoding="utf-8")
        exported += 1
    return exported


def _yaml_str(value: object) -> str:
    return str(value or "").replace('"', "").replace("\n", " ").strip()


def _parse_frontmatter_kv(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    kv: dict[str, str] = {}
    for line in parts[1].strip("\n").splitlines():
        if line and not line[0].isspace() and ":" in line:
            k, v = line.split(":", 1)
            kv[k.strip()] = v.strip()
    return kv


def _frontmatter_book_id(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    raw = _parse_frontmatter_kv(text).get("book_id")
    if not raw:
        return None
    val = raw.strip().strip('"').strip("'")
    return val or None


def _book_status_label(conn: sqlite3.Connection, book: sqlite3.Row) -> str:
    try:
        row = conn.execute("SELECT status FROM book_status WHERE book_id=?", (book["book_id"],)).fetchone()
        if row and row["status"]:
            return str(row["status"])
    except sqlite3.Error:
        pass
    keys = book.keys()
    finished = book["finished"] if "finished" in keys else 0
    prog = book["progress"] if ("progress" in keys and book["progress"] is not None) else (book["reading_progress"] or 0)
    if finished == 1 or prog == 100:
        return "已读"
    if 1 <= prog <= 99:
        return "在读"
    return "未读"


def export_obsidian(
    conn: sqlite3.Connection, destination: Path, with_popular: bool = False
) -> ObsidianExportResult:
    """增量导出笔记到 Obsidian：
    - 使用 `<!-- weread-vault:begin notes -->` … `<!-- weread-vault:end notes -->` 管理区块。
    - 标记区块外的任何手写文字一个字不动；区块内已存在条目不改不删，只在 end 前追加新条目。
    - 用户删掉的条目通过 `obsidian_exported` 表记录，不会重新加回。
    - frontmatter 管理字段每次刷新，用户自加字段原样保留。
    - 内容无变化不写文件（不改 mtime）。
    """
    destination.mkdir(parents=True, exist_ok=True)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS obsidian_exported (
          book_id TEXT NOT NULL,
          item_id TEXT NOT NULL,
          exported_at INTEGER NOT NULL,
          PRIMARY KEY (book_id, item_id)
        )"""
    )
    existing_by_book_id: dict[str, Path] = {}
    names: dict[str, str] = {}
    for md_file in sorted(destination.glob("*.md")):
        bid = _frontmatter_book_id(md_file)
        if bid:
            existing_by_book_id[bid] = md_file
            names[md_file.stem] = bid

    books = conn.execute("SELECT * FROM books WHERE total_notes > 0 ORDER BY sort DESC").fetchall()
    written = 0
    created_count = 0
    appended_count = 0
    new_items_total = 0
    now_ts = int(time.time())
    today_str = time.strftime("%Y-%m-%d", time.localtime(now_ts))

    for book in books:
        book_id = str(book["book_id"])
        highlights = conn.execute(
            "SELECT * FROM highlights WHERE book_id=? ORDER BY chapter_uid, text_range, create_time",
            (book_id,),
        ).fetchall()
        thoughts = conn.execute(
            "SELECT * FROM thoughts WHERE book_id=? ORDER BY is_book_review DESC, chapter_uid, create_time",
            (book_id,),
        ).fetchall()
        popular = (
            conn.execute(
                "SELECT * FROM popular_highlights WHERE book_id=? ORDER BY chapter_uid, text_range",
                (book_id,),
            ).fetchall()
            if with_popular
            else []
        )
        if not highlights and not thoughts and not popular:
            continue

        if book_id in existing_by_book_id:
            path = existing_by_book_id[book_id]
            names[path.stem] = book_id
        else:
            filename = _safe_name(book["title"])
            candidate = destination / f"{filename}.md"
            if (filename in names and names[filename] != book_id) or (
                candidate.exists() and existing_by_book_id.get(book_id) != candidate
            ):
                filename = f"{filename}-{book_id}"
            names[filename] = book_id
            path = destination / f"{filename}.md"
            existing_by_book_id[book_id] = path

        file_existed = path.exists()
        old_text = path.read_text(encoding="utf-8") if file_existed else ""
        old_fm_kv = _parse_frontmatter_kv(old_text) if file_existed else {}

        exported_ids = {
            str(r[0])
            for r in conn.execute("SELECT item_id FROM obsidian_exported WHERE book_id=?", (book_id,)).fetchall()
        }
        if file_existed:
            file_wv_ids = set(re.findall(r"<!--\s*wv:([^\s>]+)\s*-->", old_text))
            already_exported = exported_ids | file_wv_ids
        else:
            file_wv_ids = set()
            already_exported = set()

        candidates: list[tuple[str, str, list[str]]] = []
        # Document order (chapter, numeric position) so a thought lands right after its highlight;
        # text_range is a string, so SQL ORDER BY would sort "1096-" before "914-".
        order: dict[str, tuple[int, int, int, int]] = {}
        highlight_ranges: dict[str, str] = {}
        thought_ranges: dict[str, str] = {}
        for h in highlights:
            item_id = str(h["bookmark_id"])
            h_keys = h.keys()
            order[item_id] = (int(h["chapter_uid"] or 0), _position(h["text_range"], h["page"] if "page" in h_keys else None),
                              0, int(h["create_time"] or 0))
            if h["text_range"]:
                highlight_ranges[item_id] = f"{h['chapter_uid']}:{h['text_range']}"
            elif h["mark_text"]:  # paper notes have no range: pair by page + quoted text
                highlight_ranges[item_id] = f"text:{h['page'] if 'page' in h_keys else ''}:{h['mark_text']}"
            chapter = (
                h["chapter_title"]
                or (f"p.{h['page']}" if ("page" in h_keys and h["page"]) else "")
                or ""
            )
            candidates.append((item_id, chapter, [f"<!-- wv:{item_id} -->", f"> {h['mark_text'] or ''}"]))

        for t in thoughts:
            item_id = str(t["review_id"])
            t_keys = t.keys()
            order[item_id] = (-1 if t["is_book_review"] and not t["abstract"] else int(t["chapter_uid"] or 0),
                              _position(t["text_range"], t["page"] if "page" in t_keys else None),
                              1, int(t["create_time"] or 0))
            if t["abstract"] and t["text_range"]:
                thought_ranges[item_id] = f"{t['chapter_uid']}:{t['text_range']}"
            elif t["abstract"]:
                thought_ranges[item_id] = f"text:{t['page'] if 'page' in t_keys else ''}:{t['abstract']}"
            chapter = (
                t["chapter_name"]
                or (f"p.{t['page']}" if ("page" in t_keys and t["page"]) else ("书评" if t["is_book_review"] else ""))
                or ""
            )
            if t["abstract"]:
                item_lines = [
                    f"<!-- wv:{item_id} -->",
                    f"> {t['abstract']}",
                    f"💭 {t['content'] or ''}",
                ]
            else:
                item_lines = [
                    f"<!-- wv:{item_id} -->",
                    f"💭 {t['content'] or ''}",
                ]
            candidates.append((item_id, chapter, item_lines))

        for p in popular:
            item_id = f"pop:{p['chapter_uid']}:{p['text_range']}"
            order[item_id] = (int(p["chapter_uid"] or 0), _position(p["text_range"], None), 2, 0)
            chapter = p["chapter_title"] or ""
            item_lines = [
                f"<!-- wv:{item_id} -->",
                f"- 🔥 {p['mark_text'] or ''} <small>（{p['count'] or 0} 人划线）</small>",
            ]
            candidates.append((item_id, chapter, item_lines))

        new_entries = [entry for entry in candidates if entry[0] not in already_exported]
        new_entries.sort(key=lambda entry: order.get(entry[0], (0, 0, 0, 0)))
        # A thought on a highlight written in this same batch sits right under it, so drop the
        # duplicated quote line; otherwise (highlight exported earlier) keep "> 原文" for context.
        fresh_ranges = {highlight_ranges[e[0]] for e in new_entries if e[0] in highlight_ranges}
        new_entries = [
            (item_id, chapter,
             [line for line in lines if not (thought_ranges.get(item_id) in fresh_ranges and line.startswith("> "))])
            for item_id, chapter, lines in new_entries
        ]

        b_keys = book.keys()
        is_paper = ("source" in b_keys and book["source"] == "paper") or book_id.startswith("PAPER_")
        source_label = "纸质书" if is_paper else "微信读书"
        progress = (
            book["progress"]
            if ("progress" in b_keys and book["progress"] is not None)
            else (book["reading_progress"] or 0)
        )
        status_label = _book_status_label(conn, book)
        reading_seconds = (book["reading_seconds"] if "reading_seconds" in b_keys else 0) or 0
        reading_hours = round(int(reading_seconds) / 3600, 1)
        finish_time = book["finish_time"] if "finish_time" in b_keys else None
        finish_date = _date(finish_time)
        rating_val = book["rating"] if ("rating" in b_keys and book["rating"] is not None) else None
        rating_str = str(rating_val) if rating_val is not None else '""'
        isbn_str = _yaml_str(book["isbn"] if "isbn" in b_keys else "")
        publisher_str = _yaml_str(book["publisher"] if "publisher" in b_keys else "")
        reader_link = _yaml_str(book["reader_link"] if "reader_link" in b_keys else "")

        existing_updated = old_fm_kv.get("updated", "").strip('"').strip("'")
        updated_str = existing_updated if (file_existed and not new_entries and existing_updated) else today_str

        def _build_fm(upd: str) -> list[str]:
            return [
                "---",
                f'title: "{_yaml_str(book["title"])}"',
                f'author: "{_yaml_str(book["author"])}"',
                f'book_id: "{book_id}"',
                f'source: "{source_label}"',
                f'category: "{_yaml_str(book["category"])}"',
                f'cover: "{_yaml_str(book["cover"])}"',
                f'isbn: "{isbn_str}"',
                f'publisher: "{publisher_str}"',
                f"rating: {rating_str}",
                f"progress: {progress}",
                f'status: "{status_label}"',
                f"reading_hours: {reading_hours}",
                f'finish_date: "{finish_date}"',
                f"highlights: {len(highlights)}",
                f"thoughts: {len(thoughts)}",
                f'reader_link: "{reader_link}"',
                f'updated: "{upd}"',
                *_user_frontmatter(path, managed=_OBSIDIAN_MANAGED_FRONTMATTER),
                "---",
            ]

        if not file_existed:
            rendered_items: list[str] = []
            current_chapter = ""
            for _item_id, chapter, item_lines in new_entries:
                if chapter and chapter != current_chapter:
                    rendered_items.extend([f"### {chapter}", ""])
                    current_chapter = chapter
                rendered_items.extend([*item_lines, ""])
            if rendered_items and rendered_items[-1] == "":
                rendered_items.pop()

            fm_lines = _build_fm(today_str)
            body_lines = [
                "",
                f"# {book['title'] or '未命名'}",
                "",
                *([f"[打开阅读]({reader_link})", ""] if reader_link else []),
                "## 我的笔记",
                "",
                BEGIN_NOTES,
                *rendered_items,
                END_NOTES,
                "",
            ]
            content = "\n".join([*fm_lines, *body_lines])
            path.write_text(content, encoding="utf-8")
            with conn:
                conn.executemany(
                    "INSERT OR IGNORE INTO obsidian_exported(book_id, item_id, exported_at) VALUES (?, ?, ?)",
                    [(book_id, item_id, now_ts) for item_id, _, _ in candidates],
                )
            written += 1
            created_count += 1
            new_items_total += len(new_entries)
            continue

        # Existing file: keep everything outside frontmatter and outside new entries untouched.
        if old_text.startswith("---"):
            parts = old_text.split("---", 2)
            body_after_fm = parts[2] if len(parts) >= 3 else "\n" + old_text
        else:
            body_after_fm = "\n" + old_text

        if new_entries:
            begin_idx = body_after_fm.find(BEGIN_NOTES)
            end_idx = body_after_fm.find(END_NOTES)
            current_chapter = ""
            if begin_idx != -1 and end_idx != -1 and begin_idx < end_idx:
                block_inner = body_after_fm[begin_idx + len(BEGIN_NOTES) : end_idx]
                headings = re.findall(r"^###\s+(.+?)\s*$", block_inner, flags=re.MULTILINE)
                if headings:
                    current_chapter = headings[-1].strip()

            rendered_items = []
            for _item_id, chapter, item_lines in new_entries:
                if chapter and chapter != current_chapter:
                    rendered_items.extend([f"### {chapter}", ""])
                    current_chapter = chapter
                rendered_items.extend([*item_lines, ""])
            if rendered_items and rendered_items[-1] == "":
                rendered_items.pop()
            addition = "\n".join(rendered_items)

            if begin_idx != -1 and end_idx != -1 and begin_idx < end_idx:
                before_end = body_after_fm[:end_idx]
                after_end = body_after_fm[end_idx:]
                inner_stripped = body_after_fm[begin_idx + len(BEGIN_NOTES) : end_idx].strip()
                if not before_end.endswith("\n"):
                    before_end += "\n"
                if inner_stripped and not before_end.endswith("\n\n"):
                    before_end += "\n"
                body_after_fm = f"{before_end}{addition}\n{after_end}"
            else:
                if not body_after_fm.endswith("\n"):
                    body_after_fm += "\n"
                body_after_fm += f"\n{BEGIN_NOTES}\n{addition}\n{END_NOTES}\n"

        candidate_content = "\n".join(_build_fm(updated_str)) + body_after_fm
        if not new_entries and candidate_content == old_text:
            if file_wv_ids - exported_ids:
                with conn:
                    conn.executemany(
                        "INSERT OR IGNORE INTO obsidian_exported(book_id, item_id, exported_at) VALUES (?, ?, ?)",
                        [(book_id, item_id, now_ts) for item_id in (file_wv_ids - exported_ids)],
                    )
            continue

        # Either new_entries were added or managed frontmatter changed -> refresh updated to today_str
        final_content = "\n".join(_build_fm(today_str)) + body_after_fm
        if final_content == old_text:
            continue
        path.write_text(final_content, encoding="utf-8")
        with conn:
            conn.executemany(
                "INSERT OR IGNORE INTO obsidian_exported(book_id, item_id, exported_at) VALUES (?, ?, ?)",
                [(book_id, item_id, now_ts) for item_id in ({e[0] for e in new_entries} | file_wv_ids)],
            )
        written += 1
        if new_entries:
            appended_count += 1
            new_items_total += len(new_entries)

    return ObsidianExportResult(
        written, created=created_count, appended=appended_count, new_items=new_items_total
    )
