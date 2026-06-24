from __future__ import annotations

import sqlite3
import time
from pathlib import Path


SCHEMA_VERSION = 3

# Columns added after v1 (rich /book/info metadata). Added idempotently to existing
# databases via PRAGMA table_info so upgrading never drops data.
_BOOK_EXTRA_COLUMNS = {
    "rating": "REAL", "rating_count": "INTEGER", "word_count": "INTEGER",
    "publisher": "TEXT", "isbn": "TEXT", "translator": "TEXT",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS books (
  book_id TEXT PRIMARY KEY,
  title TEXT,
  author TEXT,
  cover TEXT,
  intro TEXT,
  category TEXT,
  publish_time TEXT,
  review_count INTEGER NOT NULL DEFAULT 0,
  note_count INTEGER NOT NULL DEFAULT 0,
  bookmark_count INTEGER NOT NULL DEFAULT 0,
  total_notes INTEGER NOT NULL DEFAULT 0,
  reading_progress INTEGER,
  marked_status INTEGER,
  finished INTEGER,
  sort INTEGER,
  notes_synced_sort INTEGER,
  rating REAL,
  rating_count INTEGER,
  word_count INTEGER,
  publisher TEXT,
  isbn TEXT,
  translator TEXT,
  synced_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS highlights (
  bookmark_id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
  chapter_uid INTEGER,
  chapter_title TEXT,
  mark_text TEXT,
  text_range TEXT,
  color_style INTEGER,
  create_time INTEGER,
  updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS thoughts (
  review_id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
  chapter_uid INTEGER,
  chapter_name TEXT,
  content TEXT,
  star INTEGER,
  text_range TEXT,
  is_book_review INTEGER NOT NULL DEFAULT 0,
  create_time INTEGER,
  updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS reading_stats (
  id INTEGER PRIMARY KEY,
  mode TEXT NOT NULL,
  base_time INTEGER NOT NULL DEFAULT 0,
  payload TEXT NOT NULL,
  fetched_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sync_runs (
  id INTEGER PRIMARY KEY,
  started_at INTEGER NOT NULL,
  completed_at INTEGER,
  status TEXT NOT NULL,
  scope TEXT NOT NULL,
  detail TEXT
);
CREATE TABLE IF NOT EXISTS sync_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS popular_highlights (
  book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
  chapter_uid INTEGER,
  chapter_title TEXT,
  mark_text TEXT,
  text_range TEXT,
  count INTEGER,
  synced_at INTEGER NOT NULL,
  PRIMARY KEY (book_id, text_range)
);
CREATE INDEX IF NOT EXISTS idx_pop_book ON popular_highlights(book_id);
CREATE INDEX IF NOT EXISTS idx_books_sort ON books(sort DESC);
CREATE INDEX IF NOT EXISTS idx_highlights_book ON highlights(book_id);
CREATE INDEX IF NOT EXISTS idx_thoughts_book ON thoughts(book_id);
CREATE INDEX IF NOT EXISTS idx_stats_mode_time ON reading_stats(mode, fetched_at DESC);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def _ensure_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(books)")}
    for name, sqltype in _BOOK_EXTRA_COLUMNS.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE books ADD COLUMN {name} {sqltype}")  # name/type are internal constants


def initialize(path: Path) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        _ensure_columns(conn)
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, int(time.time())),
        )


def set_state(conn: sqlite3.Connection, key: str, value: str) -> None:
    now = int(time.time())
    updated = conn.execute(
        "UPDATE sync_state SET value=?, updated_at=? WHERE key=?", (value, now, key)
    )
    if updated.rowcount == 0:
        conn.execute("INSERT INTO sync_state(key, value, updated_at) VALUES (?, ?, ?)", (key, value, now))


def get_state(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM sync_state WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def summary(conn: sqlite3.Connection) -> dict[str, int | str | None]:
    values = dict(
        conn.execute(
            """SELECT
              (SELECT count(*) FROM books) AS books,
              (SELECT count(*) FROM highlights) AS highlights,
              (SELECT count(*) FROM thoughts) AS thoughts,
              (SELECT max(completed_at) FROM sync_runs WHERE status='success') AS last_success,
              (SELECT max(completed_at) FROM sync_runs WHERE status='failed') AS last_failure"""
        ).fetchone()
    )
    return values
