#!/usr/bin/env python3
"""Deterministic fake WeRead data for docs and demos."""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from weread_vault.db import initialize  # noqa: E402


BOOKS = [
    ("sample-001", "星河笔记：在夜航中思考", "林小满", "工具与效率", "#2563eb", "#7c3aed", 87, 12),
    ("sample-002", "慢读花园", "周青禾", "文学随笔", "#059669", "#14b8a6", 64, 8),
    ("sample-003", "纸上城市漫游", "陈亦舟", "文学随笔", "#dc2626", "#f97316", 42, 5),
    ("sample-004", "把时间折成书签", "顾南风", "工具与效率", "#9333ea", "#ec4899", 95, 18),
    ("sample-005", "一杯茶里的宇宙", "宋知夏", "科学通识", "#0f766e", "#65a30d", 31, 3),
    ("sample-006", "清晨算法课", "许明远", "科学通识", "#0369a1", "#38bdf8", 76, 15),
    ("sample-007", "灯下的长期主义", "叶澜", "心理成长", "#ca8a04", "#f59e0b", 54, 6),
    ("sample-008", "海边书店来信", "白鹿", "文学随笔", "#db2777", "#fb7185", 22, 2),
    ("sample-009", "示例小说：风从第七页来", "赵栖迟", "文学随笔", "#4f46e5", "#06b6d4", 68, 9),
    ("sample-010", "索引与星图", "孟遥", "工具与效率", "#475569", "#64748b", 48, 7),
    ("sample-011", "假日观察手册", "何西", "心理成长", "#ea580c", "#facc15", 83, 11),
    ("sample-012", "给未来的阅读报告", "沈安", "工具与效率", "#16a34a", "#84cc16", 39, 4),
    ("sample-101", "私人知识库小史", "林小满", "工具与效率", "#1d4ed8", "#22c55e", 0, 0),
    ("sample-102", "离线工具的温度", "林小满", "工具与效率", "#7c2d12", "#f97316", 0, 0),
    ("sample-103", "给 Agent 的索引课", "林小满", "工具与效率", "#581c87", "#a855f7", 0, 0),
    ("sample-104", "慢慢同步", "林小满", "工具与效率", "#0f766e", "#14b8a6", 0, 0),
    ("sample-105", "笔记与边界", "林小满", "工具与效率", "#be123c", "#fb7185", 0, 0),
    ("sample-106", "每周读书实验", "林小满", "工具与效率", "#334155", "#94a3b8", 0, 0),
]

HIGHLIGHTS = [
    ("sample-001", 1, "序章 为什么要保存阅读现场", "真正重要的不是读过多少，而是那些被你反复想起的句子。", "2026-06-01", 5),
    ("sample-001", 2, "第一章 本地优先", "把数据放回自己手里，工具才会变成长期可依赖的基础设施。", "2026-06-03", 4),
    ("sample-001", 3, "第二章 搜索与回看", "笔记的价值常常在第二次相遇时出现。", "2026-06-04", 3),
    ("sample-001", 4, "第三章 与 AI 协作", "让 agent 读取结构化笔记，而不是让记忆散落在聊天记录里。", "2026-06-05", 5),
]

POPULAR = [
    ("sample-001", 1, "序章 为什么要保存阅读现场", "当阅读记录可以被检索，过去的自己就会变成一个安静的协作者。", 284),
    ("sample-001", 2, "第一章 本地优先", "本地数据库的意义，是让私人知识不必为了便利而失去边界。", 197),
    ("sample-001", 3, "第二章 搜索与回看", "好的归档不是收藏，而是在需要时把线索送回眼前。", 163),
    ("sample-001", 4, "第三章 与 AI 协作", "AI 读结构化数据时，回答会少一点猜测，多一点证据。", 121),
]

PUBLIC_REVIEWS = [
    ("sample-001", "演示用户 A", "这本示例书把“本地优先”和“长期归档”讲得很清楚，适合给工具型产品做说明。", 5, 42),
    ("sample-001", "演示用户 B", "章节短，观点密度高，读完很容易整理成自己的工作流。", 4, 18),
    ("sample-001", "演示用户 C", "最有启发的是把笔记当作可查询数据库，而不是静态文本。", 5, 31),
]


def ts(date: str) -> int:
    return int(time.mktime(time.strptime(date, "%Y-%m-%d")))


def stats_payload() -> dict[str, object]:
    longest = [
        {"book": {"title": "星河笔记：在夜航中思考", "author": "林小满"}, "readTime": 7400},
        {"book": {"title": "慢读花园", "author": "周青禾"}, "readTime": 5200},
        {"book": {"title": "清晨算法课", "author": "许明远"}, "readTime": 3900},
        {"book": {"title": "灯下的长期主义", "author": "叶澜"}, "readTime": 2600},
    ]
    categories = [
        {"categoryTitle": "工具与效率", "readingTime": 15000, "readingCount": 8},
        {"categoryTitle": "文学随笔", "readingTime": 9100, "readingCount": 7},
        {"categoryTitle": "科学通识", "readingTime": 6300, "readingCount": 5},
        {"categoryTitle": "心理成长", "readingTime": 4200, "readingCount": 4},
    ]
    return {
        "totalReadTime": 153000,
        "readDays": 36,
        "readTimes": {"1735660800": 64800, "1767196800": 88200},
        "readLongest": longest,
        "preferCategory": categories,
        "preferAuthor": [
            {"name": "林小满", "count": 9, "readTime": "9 次"},
            {"name": "周青禾", "count": 6, "readTime": "6 次"},
            {"name": "陈亦舟", "count": 4, "readTime": "4 次"},
            {"name": "顾南风", "count": 3, "readTime": "3 次"},
        ],
        "preferTime": [0, 0, 0, 0, 0, 0, 1, 3, 5, 4, 3, 2, 2, 4, 6, 8, 7, 5, 4, 3, 2, 1, 0, 0],
        "readStat": [{"stat": "读过", "counts": "24本"}],
        "preferCategoryWord": "工具与效率",
        "preferTimeWord": "傍晚阅读较多",
    }


def create_sample_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    initialize(path)
    conn = sqlite3.connect(path)
    try:
        now = ts("2026-06-26")
        conn.executescript(
            """
            CREATE TABLE sample_book_styles (
              book_id TEXT PRIMARY KEY,
              color1 TEXT NOT NULL,
              color2 TEXT NOT NULL
            );
            CREATE TABLE sample_public_reviews (
              book_id TEXT NOT NULL,
              author TEXT NOT NULL,
              content TEXT NOT NULL,
              stars INTEGER NOT NULL,
              likes INTEGER NOT NULL
            );
            """
        )
        for index, (book_id, title, author, category, color1, color2, progress, notes) in enumerate(BOOKS):
            conn.execute(
                """INSERT INTO books(
                  book_id,title,author,cover,intro,category,total_notes,reading_progress,finished,sort,
                  rating,word_count,publisher,synced_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    book_id,
                    title,
                    author,
                    "",
                    "这是一条为截图准备的虚构书籍简介，用来展示 WeRead Vault 如何归档书籍、划线、想法和阅读统计。",
                    category,
                    notes,
                    progress,
                    1 if progress >= 80 else 0,
                    10_000 - index,
                    92.0 if book_id == "sample-001" else 80.0,
                    128000,
                    "示例出版社",
                    now,
                ),
            )
            conn.execute("INSERT INTO sample_book_styles(book_id,color1,color2) VALUES(?,?,?)", (book_id, color1, color2))

        for index, (book_id, chapter_uid, chapter, mark_text, date, color_style) in enumerate(HIGHLIGHTS, start=1):
            conn.execute(
                """INSERT INTO highlights(
                  bookmark_id,book_id,chapter_uid,chapter_title,mark_text,text_range,color_style,create_time,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    f"sample-highlight-{index}",
                    book_id,
                    chapter_uid,
                    chapter,
                    mark_text,
                    f"{chapter_uid * 100}-{chapter_uid * 100 + 20}",
                    color_style,
                    ts(date),
                    now,
                ),
            )

        conn.execute(
            """INSERT INTO thoughts(
              review_id,book_id,chapter_uid,chapter_name,content,star,text_range,is_book_review,create_time,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                "sample-thought-1",
                "sample-001",
                4,
                "第三章 与 AI 协作",
                "结构化笔记适合交给 agent 做检索和复盘，但原始数据仍应留在本机。",
                5,
                "420-450",
                0,
                ts("2026-06-05"),
                now,
            ),
        )

        for index, (book_id, chapter_uid, chapter, mark_text, count) in enumerate(POPULAR, start=1):
            conn.execute(
                """INSERT INTO popular_highlights(
                  book_id,chapter_uid,chapter_title,mark_text,text_range,count,synced_at
                ) VALUES(?,?,?,?,?,?,?)""",
                (book_id, chapter_uid, chapter, mark_text, f"{chapter_uid * 1000}-{chapter_uid * 1000 + index}", count, now),
            )

        conn.executemany(
            "INSERT INTO sample_public_reviews(book_id,author,content,stars,likes) VALUES(?,?,?,?,?)",
            PUBLIC_REVIEWS,
        )

        payload = stats_payload()
        for mode in ("overall", "annually", "monthly", "weekly"):
            conn.execute(
                "INSERT INTO reading_stats(mode, base_time, payload, fetched_at) VALUES(?,?,?,?)",
                (mode, 0, json.dumps(payload, ensure_ascii=False), now),
            )
        conn.execute(
            "INSERT INTO sync_runs(started_at, completed_at, status, scope, detail) VALUES(?,?,?,?,?)",
            (now - 20, now, "success", "sample", "generated fake sample data"),
        )
        conn.commit()
    finally:
        conn.close()


def dump_sql(db_path: Path, sql_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        sql_path.parent.mkdir(parents=True, exist_ok=True)
        sql_path.write_text("\n".join(conn.iterdump()) + "\n", encoding="utf-8")
    finally:
        conn.close()
