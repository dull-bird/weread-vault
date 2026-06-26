#!/usr/bin/env python3
"""Generate privacy-safe sample screenshots for the docs.

The screenshots are static marketing/docs assets. They are rendered from a
deterministic sample database: book metadata comes from the sample seed, while
notes, thoughts, reading stats, progress, and activity are generated demo data
so the public site never exposes private highlights or reading history.

Requirements:
  - Google Chrome / Chromium available on PATH, or set CHROME=/path/to/chrome
  - A Chinese font such as Noto Sans CJK SC installed for best rendering

Run from the repository root:
  python3 scripts/generate-sample-doc-assets.py
"""

from __future__ import annotations

import html
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
SAMPLE_SQL = ROOT / "docs" / "sample-data" / "weread-vault-sample.sql"
FONT = "Noto Sans CJK SC, Microsoft YaHei, Arial, sans-serif"

BOOKS = [
    ("星河笔记：在夜航中思考", "林小满", "#2563eb", "#7c3aed", 87, 12),
    ("慢读花园", "周青禾", "#059669", "#14b8a6", 64, 8),
    ("纸上城市漫游", "陈亦舟", "#dc2626", "#f97316", 42, 5),
    ("把时间折成书签", "顾南风", "#9333ea", "#ec4899", 95, 18),
    ("一杯茶里的宇宙", "宋知夏", "#0f766e", "#65a30d", 31, 3),
    ("清晨算法课", "许明远", "#0369a1", "#38bdf8", 76, 15),
    ("灯下的长期主义", "叶澜", "#ca8a04", "#f59e0b", 54, 6),
    ("海边书店来信", "白鹿", "#db2777", "#fb7185", 22, 2),
    ("示例小说：风从第七页来", "赵栖迟", "#4f46e5", "#06b6d4", 68, 9),
    ("索引与星图", "孟遥", "#475569", "#64748b", 48, 7),
    ("假日观察手册", "何西", "#ea580c", "#facc15", 83, 11),
    ("给未来的阅读报告", "沈安", "#16a34a", "#84cc16", 39, 4),
]

NOTES = [
    ("序章 为什么要保存阅读现场", "真正重要的不是读过多少，而是那些被你反复想起的句子。", "2026-06-01", 5),
    ("第一章 本地优先", "把数据放回自己手里，工具才会变成长期可依赖的基础设施。", "2026-06-03", 4),
    ("第二章 搜索与回看", "笔记的价值常常在第二次相遇时出现。", "2026-06-04", 3),
    ("第三章 与 AI 协作", "让 agent 读取结构化笔记，而不是让记忆散落在聊天记录里。", "2026-06-05", 5),
]

POPULAR = [
    ("序章 为什么要保存阅读现场", "当阅读记录可以被检索，过去的自己就会变成一个安静的协作者。", 284),
    ("第一章 本地优先", "本地数据库的意义，是让私人知识不必为了便利而失去边界。", 197),
    ("第二章 搜索与回看", "好的归档不是收藏，而是在需要时把线索送回眼前。", 163),
    ("第三章 与 AI 协作", "AI 读结构化数据时，回答会少一点猜测，多一点证据。", 121),
]

REVIEWS = [
    ("演示用户 A", "这本示例书把“本地优先”和“长期归档”讲得很清楚，适合给工具型产品做说明。", 5, 42),
    ("演示用户 B", "章节短，观点密度高，读完很容易整理成自己的工作流。", 4, 18),
    ("演示用户 C", "最有启发的是把笔记当作可查询数据库，而不是静态文本。", 5, 31),
]

SIMILAR = [
    ("私人知识库小史", "林小满", "#1d4ed8", "#22c55e"),
    ("离线工具的温度", "林小满", "#7c2d12", "#f97316"),
    ("给 Agent 的索引课", "林小满", "#581c87", "#a855f7"),
    ("慢慢同步", "林小满", "#0f766e", "#14b8a6"),
    ("笔记与边界", "林小满", "#be123c", "#fb7185"),
    ("每周读书实验", "林小满", "#334155", "#94a3b8"),
]

STATS_LONGEST = [("星河笔记：在夜航中思考", 7400), ("慢读花园", 5200), ("清晨算法课", 3900), ("灯下的长期主义", 2600)]
STATS_CATEGORIES = [("工具与效率", 15000), ("文学随笔", 9100), ("科学通识", 6300), ("心理成长", 4200)]
STATS_AUTHORS = [("林小满", 9), ("周青禾", 6), ("陈亦舟", 4), ("顾南风", 3)]
STATS_SESSIONS = [("≤5 分钟", 3), ("5-15 分钟", 6), ("15-30 分钟", 9), ("30-60 分钟", 5)]


def load_sample_data(sql_path: Path = SAMPLE_SQL) -> None:
    if not sql_path.exists():
        raise SystemExit(f"Sample SQL not found: {sql_path}. Run scripts/create-sample-db.py --sql {sql_path}")

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(sql_path.read_text(encoding="utf-8"))
        first_book = "sample-001"
        global BOOKS, NOTES, POPULAR, REVIEWS, SIMILAR
        global STATS_LONGEST, STATS_CATEGORIES, STATS_AUTHORS, STATS_SESSIONS

        BOOKS = [
            (
                row["title"],
                row["author"],
                row["color1"],
                row["color2"],
                int(row["reading_progress"] or 0),
                int(row["total_notes"] or 0),
            )
            for row in conn.execute(
                """SELECT b.title,b.author,s.color1,s.color2,b.reading_progress,b.total_notes
                FROM books b JOIN sample_book_styles s USING(book_id)
                WHERE b.book_id < 'sample-100'
                ORDER BY b.sort DESC
                LIMIT 12"""
            )
        ]
        NOTES = [
            (row["chapter_title"], row["mark_text"], row["d"], int(row["color_style"] or 0))
            for row in conn.execute(
                """SELECT chapter_title,mark_text,date(create_time,'unixepoch') AS d,color_style
                FROM highlights WHERE book_id=? ORDER BY chapter_uid, create_time""",
                (first_book,),
            )
        ]
        POPULAR = [
            (row["chapter_title"], row["mark_text"], int(row["count"] or 0))
            for row in conn.execute(
                """SELECT chapter_title,mark_text,count
                FROM popular_highlights WHERE book_id=? ORDER BY chapter_uid""",
                (first_book,),
            )
        ]
        REVIEWS = [
            (row["author"], row["content"], int(row["stars"] or 0), int(row["likes"] or 0))
            for row in conn.execute(
                "SELECT author,content,stars,likes FROM sample_public_reviews WHERE book_id=? ORDER BY likes DESC",
                (first_book,),
            )
        ]
        author = conn.execute("SELECT author FROM books WHERE book_id=?", (first_book,)).fetchone()["author"]
        SIMILAR = [
            (row["title"], row["author"], row["color1"], row["color2"])
            for row in conn.execute(
                """SELECT b.title,b.author,s.color1,s.color2
                FROM books b JOIN sample_book_styles s USING(book_id)
                WHERE b.author=? AND b.book_id<>?
                ORDER BY b.sort DESC
                LIMIT 6""",
                (author, first_book),
            )
        ]

        payload_row = conn.execute("SELECT payload FROM reading_stats WHERE mode='overall' ORDER BY fetched_at DESC LIMIT 1").fetchone()
        if payload_row:
            payload = json.loads(payload_row["payload"])
            STATS_LONGEST = [
                ((item.get("book") or {}).get("title") or "", int(item.get("readTime") or 0))
                for item in payload.get("readLongest", [])[:4]
            ]
            STATS_CATEGORIES = [
                (item.get("categoryTitle") or "", int(item.get("readingTime") or 0))
                for item in payload.get("preferCategory", [])[:4]
            ]
            STATS_AUTHORS = [
                (item.get("name") or "", int(item.get("count") or 0))
                for item in payload.get("preferAuthor", [])[:4]
            ]
    finally:
        conn.close()


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def wrap_text(value: str, max_chars: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in value:
        if char == "\n" or len(current) >= max_chars:
            if current:
                lines.append(current)
            current = "" if char == "\n" else char
        else:
            current += char
    if current:
        lines.append(current)
    return lines or [""]


def text(
    x: float,
    y: float,
    value: object,
    size: int = 24,
    weight: int = 400,
    fill: str = "#11161d",
    anchor: str = "start",
) -> str:
    return (
        f"<text x='{x}' y='{y}' font-size='{size}' font-weight='{weight}' "
        f"fill='{fill}' text-anchor='{anchor}'>{esc(value)}</text>"
    )


def multiline(
    x: float,
    y: float,
    value: str,
    size: int = 24,
    fill: str = "#11161d",
    max_chars: int = 24,
    line_h: int = 34,
    weight: int = 400,
    anchor: str = "start",
) -> str:
    return "".join(
        text(x, y + i * line_h, line, size, weight, fill, anchor)
        for i, line in enumerate(wrap_text(value, max_chars))
    )


def rect(x: float, y: float, w: float, h: float, rx: int = 0, fill: str = "#fff", stroke: str = "none") -> str:
    return f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='{rx}' fill='{fill}' stroke='{stroke}'/>"


def badge(x: float, y: float, label: str, fill: str = "#eef6ff", color: str = "#1556e0") -> str:
    width = 28 + len(label) * 15
    stroke = "#e7e9ee" if fill == "#fff" else "none"
    return rect(x, y, width, 38, 19, fill, stroke) + text(x + 14, y + 25, label, 18, 600, color)


def progress(x: float, y: float, width: float, pct: int, color1: str = "#1556e0", color2: str = "#7c3aed") -> str:
    gid = f"g{abs(hash((x, y, width, pct, color1, color2))) % 1_000_000}"
    return (
        f"<defs><linearGradient id='{gid}' x1='0' x2='1'>"
        f"<stop stop-color='{color1}'/><stop offset='1' stop-color='{color2}'/>"
        f"</linearGradient></defs>"
        + rect(x, y, width, 8, 4, "#e7e9ee")
        + rect(x, y, width * pct / 100, 8, 4, f"url(#{gid})")
    )


def cover(x: float, y: float, width: float, height: float, title: str, color1: str, color2: str, small: bool = False) -> str:
    gid = f"c{abs(hash((title, color1, color2))) % 1_000_000}"
    size = 20 if small else 30
    max_chars = 7 if small else 8
    return f"""
    <defs><linearGradient id='{gid}' x1='0' y1='0' x2='1' y2='1'>
      <stop stop-color='{color1}'/><stop offset='1' stop-color='{color2}'/>
    </linearGradient></defs>
    {rect(x, y, width, height, 12, f"url(#{gid})")}
    {rect(x + 16, y + 16, width - 32, height - 32, 8, "rgba(255,255,255,.16)")}
    {multiline(x + width / 2, y + height * 0.34, title, size, "#fff", max_chars, size + 8, 800, "middle")}
    {text(x + width / 2, y + height - 34, "示例书籍", 16, 600, "rgba(255,255,255,.86)", "middle")}
    """


def shell(width: int, height: int, body: str, view: str = "0 0 2400 1640") -> str:
    return f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='{view}'>
<style>text{{font-family:{FONT};dominant-baseline:auto}}svg{{background:#f6f7f9}}</style>
{rect(0, 0, 2400, 1640, 0, "#f6f7f9")}
{body}
</svg>"""


def sidebar(height: int = 1640) -> str:
    items = [("书架", 160, True), ("阅读统计", 250, False), ("搜索 / 书城", 340, False), ("同步设置", 430, False)]
    svg = rect(0, 0, 420, height, 0, "#fbfcfd", "#e7e9ee")
    svg += text(48, 80, "WeRead", 34, 800)
    svg += text(188, 80, "Vault", 34, 800, "#1556e0")
    for label, y, active in items:
        svg += rect(28, y - 36, 344, 78, 16, "#dce8ff" if active else "transparent")
        svg += text(88, y, label, 25, 700 if active else 600, "#1556e0" if active else "#11161d")
    svg += text(48, height - 110, "示例数据 · 不含真实阅读记录", 21, 500, "#69707b")
    return svg


def panel_bar(x: int, y: int, width: int, height: int, title: str, items: list[tuple[str, int]]) -> str:
    svg = rect(x, y, width, height, 16, "#fff", "#e7e9ee") + text(x + 28, y + 48, title, 25, 700, "#69707b")
    max_value = max(value for _, value in items) or 1
    yy = y + 94
    for name, value in items:
        display = f"{round(value / 3600, 1)}h" if value > 100 else f"{value} 次"
        svg += text(x + 28, yy, name, 23, 500)
        svg += rect(x + 270, yy - 18, width - 420, 14, 7, "#e7e9ee")
        svg += rect(x + 270, yy - 18, (width - 420) * value / max_value, 14, 7, "#1556e0")
        svg += text(x + width - 42, yy, display, 21, 400, "#69707b", "end")
        yy += 56
    return svg


def chart_panel(x: int, y: int, width: int, height: int, title: str, kind: str) -> str:
    values = {
        "all": [18, 22, 26, 31, 38, 42],
        "year": [2, 5, 4, 8, 10, 13],
        "month": [20, 35, 18, 42, 25, 48, 30, 52, 37, 60, 45, 31],
    }.get(kind, [10, 22, 14, 31])
    svg = rect(x, y, width, height, 16, "#fff", "#e7e9ee") + text(x + 28, y + 48, title, 25, 700, "#69707b")
    max_value = max(values)
    base_x = x + 80
    base_y = y + height - 70
    step = (width - 160) / len(values)
    bar_w = step * 0.56
    for i, value in enumerate(values):
        bar_h = (height - 150) * value / max_value
        xx = base_x + i * step + (step - bar_w) / 2
        svg += rect(xx, base_y - bar_h, bar_w, bar_h, 6, "#1556e0")
        svg += text(xx + bar_w / 2, base_y + 28, str(i + 1), 18, 400, "#69707b", "middle")
    return svg


def heat_panel(x: int, y: int, width: int, height: int) -> str:
    svg = rect(x, y, width, height, 16, "#fff", "#e7e9ee") + text(x + 28, y + 48, "每日划线活跃度", 25, 700, "#69707b")
    cell, gap, start_x, start_y = 16, 5, x + 80, y + 96
    colors = ["#e7e9ee", "#bfdbfe", "#93c5fd", "#60a5fa", "#2563eb"]
    for week in range(52):
        for day in range(7):
            level = (week * 3 + day * 5) % 11
            svg += rect(start_x + week * (cell + gap), start_y + day * (cell + gap), cell, cell, 3, colors[min(4, level // 3)])
    svg += text(x + 28, y + height - 38, "颜色越深，当天示例划线越多。", 21, 400, "#69707b")
    return svg


def dashboard() -> str:
    x0 = 490
    svg = sidebar() + rect(420, 0, 1980, 1640, 0, "#f6f7f9")
    for i, (label, value) in enumerate([("书籍", "24"), ("划线", "186"), ("想法", "17")]):
        x = x0 + i * 620
        svg += rect(x, 120, 560, 220, 20, "#fff", "#e7e9ee")
        svg += text(x + 42, 194, label, 28, 700, "#69707b")
        svg += text(x + 42, 284, value, 58, 800)
    svg += text(x0, 440, "书架", 38, 800) + text(x0 + 92, 440, "共 24 本 · 第 1/2 页", 26, 400, "#69707b")
    svg += badge(x0, 505, "封面", "#1556e0", "#fff")
    svg += badge(x0 + 110, 505, "列表", "#fff", "#69707b")
    svg += badge(x0 + 250, 505, "最近添加", "#fff", "#11161d")
    svg += badge(x0 + 430, 505, "全部分类（示例）", "#fff", "#11161d")
    for idx, book in enumerate(BOOKS[:12]):
        row, col = divmod(idx, 6)
        x, y = x0 + col * 314, 620 + row * 620
        title, author, color1, color2, pct, note_count = book
        svg += cover(x, y, 280, 374, title, color1, color2)
        svg += multiline(x, y + 420, title, 27, "#11161d", 9, 34, 800)
        svg += text(x, y + 512, author, 23, 400, "#69707b")
        svg += progress(x, y + 560, 280, pct)
        svg += text(x, y + 616, f"{note_count} 条笔记", 21, 400, "#69707b")
        svg += text(x + 280, y + 616, f"{pct}%", 21, 400, "#69707b", "end")
    svg += badge(2020, 55, "示例数据", "#ecfdf5", "#047857")
    return shell(2400, 1640, svg)


def detail(tab: str = "mine") -> str:
    book = BOOKS[0]
    sx, sy, sw, sh = 520, 80, 1500, 1480
    svg = sidebar() + rect(420, 0, 1980, 1640, 0, "rgba(17,24,39,.72)")
    svg += rect(sx, sy, sw, sh, 22, "#f6f7f9", "#e7e9ee") + rect(sx, sy, sw, 380, 22, "#fff", "#e7e9ee")
    svg += cover(sx + 54, sy + 54, 170, 230, book[0], book[2], book[3], True)
    svg += text(sx + 260, sy + 110, book[0], 42, 800) + text(sx + 260, sy + 160, book[1], 27, 400, "#69707b")
    svg += text(sx + 260, sy + 230, "进度", 25, 400, "#69707b") + progress(sx + 340, sy + 214, 440, 87)
    svg += text(sx + 820, sy + 230, "87%", 27, 400, "#69707b")
    svg += text(sx + 260, sy + 290, "推荐", 25, 400, "#69707b") + progress(sx + 340, sy + 274, 440, 92, "#f59e0b", "#ef4444")
    svg += text(sx + 820, sy + 290, "92%", 27, 400, "#69707b")
    svg += badge(sx + 260, sy + 322, "划线 42", "#dcfce7", "#15803d")
    svg += badge(sx + 390, sy + 322, "想法 6", "#fce7f3", "#be185d")
    svg += badge(sx + 512, sy + 322, "示例分类", "#f8fafc", "#69707b")
    svg += multiline(
        sx + 260,
        sy + 404,
        "这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。",
        25,
        "#69707b",
        43,
        36,
    )
    tabs = ["我的笔记", "热门划线", "书评", "相关推荐"]
    for i, label in enumerate(tabs):
        active = (tab == "mine" and i == 0) or (tab == "popular" and i == 1) or (tab == "reviews" and i == 2) or (tab == "similar" and i == 3)
        x = sx + 54 + i * 150
        svg += text(x, sy + 470, label, 28, 700 if active else 500, "#1556e0" if active else "#69707b")
        if active:
            svg += rect(x, sy + 492, 96, 4, 2, "#1556e0")
    svg += rect(sx, sy + 510, sw, 1, 0, "#e7e9ee")

    if tab == "mine":
        svg += rect(sx + 54, sy + 548, 210, 62, 12, "#fff", "#a7c3ff") + text(sx + 84, sy + 588, "复制 Markdown", 27, 700, "#1556e0")
        y = sy + 700
        colors = ["#9333ea", "#2563eb", "#16a34a", "#ea580c"]
        for chapter, mark, date, color_idx in NOTES:
            svg += text(sx + 54, y, chapter, 30, 800, "#1556e0") + rect(sx + 54, y + 26, 1390, 1, 0, "#e7e9ee")
            svg += rect(sx + 88, y + 64, 1300, 104, 14, "#fff") + rect(sx + 88, y + 64, 5, 104, 0, colors[color_idx % 4])
            svg += text(sx + 122, y + 128, mark, 26, 400) + text(sx + 1240, y + 128, date, 22, 400, "#69707b")
            y += 210
    elif tab == "popular":
        svg += badge(sx + 54, sy + 560, "原文顺序", "#1556e0", "#fff") + badge(sx + 178, sy + 560, "按热度", "#fff", "#69707b")
        y = sy + 640
        for chapter, mark, count in POPULAR:
            svg += rect(sx + 54, y, 1380, 128, 13, "#fff", "#e7e9ee") + rect(sx + 54, y, 5, 128, 0, "#7c3aed")
            svg += text(sx + 84, y + 55, mark, 26, 400) + text(sx + 84, y + 100, chapter, 22, 400, "#69707b")
            svg += text(sx + 1250, y + 100, f"{count} 人划线", 22, 400, "#69707b")
            y += 158
    elif tab == "reviews":
        y = sy + 570
        for author, content, stars, likes in REVIEWS:
            svg += rect(sx + 54, y, 1380, 150, 13, "#fff", "#e7e9ee")
            svg += text(sx + 84, y + 48, f"{author}  {'★' * stars}", 23, 600, "#69707b")
            svg += text(sx + 1280, y + 48, f"{likes} 赞", 22, 400, "#69707b")
            svg += multiline(sx + 84, y + 96, content, 26, "#11161d", 46, 36)
            y += 180
    else:
        y = sy + 590
        svg += text(sx + 54, y - 34, "同作者「林小满」的其他示例书", 24, 400, "#69707b")
        for i, item in enumerate(SIMILAR):
            x, yy = sx + 54 + (i % 4) * 330, y + (i // 4) * 420
            svg += cover(x, yy, 240, 320, item[0], item[2], item[3], True)
            svg += multiline(x, yy + 360, item[0], 24, "#11161d", 8, 31, 700)
    svg += badge(1780, 116, "示例数据", "#ecfdf5", "#047857")
    return shell(2400, 1640, svg)


def stats(kind: str = "all") -> str:
    x0 = 490
    svg = sidebar() + rect(420, 0, 1980, 1640, 0, "#f6f7f9")
    svg += text(x0, 92, "划线热力图" if kind == "heatmap" else "阅读统计", 38, 800)
    svg += text(x0 + 210, 92, "示例数据", 25, 500, "#69707b")
    x = x0
    for label, active in [("本周", False), ("本月", kind == "month"), ("今年", kind == "year"), ("全部", kind == "all")]:
        svg += badge(x, 135, label, "#1556e0" if active else "#fff", "#fff" if active else "#69707b")
        x += 92
    svg += rect(x0, 215, 560, 160, 18, "#fff", "#e7e9ee") + text(x0 + 34, 280, "42h 30m", 48, 800) + text(x0 + 34, 330, "累计阅读时长", 24, 400, "#69707b")
    svg += rect(x0 + 600, 215, 360, 160, 18, "#fff", "#e7e9ee") + text(x0 + 634, 280, "36", 48, 800) + text(x0 + 634, 330, "阅读天数", 24, 400, "#69707b")
    svg += rect(x0 + 1000, 215, 420, 160, 18, "#fff", "#e7e9ee") + text(x0 + 1034, 280, "1h 11m", 48, 800) + text(x0 + 1034, 330, "日均", 24, 400, "#69707b")
    svg += panel_bar(x0, 430, 700, 330, "读得最多", STATS_LONGEST)
    svg += panel_bar(x0 + 740, 430, 700, 330, "阅读偏好", STATS_CATEGORIES)
    svg += heat_panel(x0, 820, 1460, 430) if kind == "heatmap" else chart_panel(x0, 820, 1460, 430, "趋势概览", kind)
    svg += panel_bar(x0, 1290, 700, 260, "常读作者", STATS_AUTHORS)
    svg += panel_bar(x0 + 740, 1290, 700, 260, "单次阅读时长分布", STATS_SESSIONS)
    svg += badge(2020, 55, "示例数据", "#ecfdf5", "#047857")
    return shell(2400, 1640, svg)


def chrome_binary() -> str:
    candidates = [
        Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else None,
        Path(os.environ["CHROME"]).expanduser() if os.environ.get("CHROME") else None,
        Path(shutil.which("google-chrome") or ""),
        Path(shutil.which("chromium") or ""),
        Path(shutil.which("chromium-browser") or ""),
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            return str(candidate)
    raise SystemExit("Chrome/Chromium not found. Set CHROME=/path/to/chrome or pass it as the first argument.")


def render_png(chrome: str, svg: str, output: Path, width: int, height: int, view: str) -> None:
    if view != "0 0 2400 1640":
        svg = svg.replace("width='2400' height='1640' viewBox='0 0 2400 1640'", f"width='{width}' height='{height}' viewBox='{view}'")
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / f"{output.stem}.svg"
        source.write_text(svg, encoding="utf-8")
        subprocess.run(
            [
                chrome,
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                f"--window-size={width},{height}",
                f"--screenshot={output}",
                source.resolve().as_uri(),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main() -> None:
    load_sample_data()
    chrome = chrome_binary()
    OUT.mkdir(parents=True, exist_ok=True)
    assets = {
        "dashboard.png": (dashboard(), "0 0 2400 1640", 2400, 1640),
        "book-detail.png": (detail("mine"), "0 0 2400 1640", 2400, 1640),
        "detail-mine.png": (detail("mine"), "360 120 1760 1320", 1760, 1320),
        "detail-popular.png": (detail("popular"), "360 120 1760 1320", 1760, 1320),
        "detail-reviews.png": (detail("reviews"), "360 120 1760 1320", 1760, 1320),
        "detail-similar.png": (detail("similar"), "360 120 1760 1320", 1760, 1320),
        "popular-highlights.png": (detail("popular"), "0 0 2400 1640", 2400, 1640),
        "reading-stats.png": (stats("all"), "0 0 2400 1640", 2400, 1640),
        "stats-all.png": (stats("all"), "430 0 1550 1640", 1248, 1694),
        "stats-year.png": (stats("year"), "430 0 1550 1640", 1248, 1694),
        "stats-month.png": (stats("month"), "430 0 1550 1640", 1248, 1584),
        "stats-heatmap.png": (stats("heatmap"), "490 820 1460 235", 1168, 188),
    }
    for name, (svg, view, width, height) in assets.items():
        render_png(chrome, svg, OUT / name, width, height, view)
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
