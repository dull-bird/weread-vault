"""Run every configured export after a sync (Markdown/Obsidian, flomo, Notion).

The model is *configure once → auto-export*: the destinations a user has set (via the
web 导出 panel or ``weread-vault export config``) are saved in the local config, and a
successful full ``weread-vault sync`` — manual or scheduled — pushes to all of them. No
per-destination scheduling: one daily sync fans out to whatever is configured.

Each target is wrapped in a ``sync_runs`` row (scope ``export:<target>``) so
``weread-vault log`` shows it alongside the sync. Markdown is idempotent and re-scans in
full (unchanged files are skipped, mtimes untouched). flomo and Notion are append-only,
so they export incrementally: only books whose note watermark (``books.sort``) advanced
past the last successful export, tracked in ``sync_state`` under ``export_<target>_sort``.
"""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from pathlib import Path

from .config import get_config, save_config
from .db import get_state, set_state
from .export import export_markdown, export_obsidian
from .integrations import export_flomo, export_notion

Reporter = Callable[[str], None]

# The config keys the web 导出 panel already writes; the CLI reuses them verbatim.
_MARKDOWN_DIR = "export_markdown_dir"
_OBSIDIAN_DIR = "export_obsidian_dir"
_FLOMO_WEBHOOK = "flomo_webhook"
_NOTION_TOKEN = "notion_token"
_NOTION_DATABASE = "notion_database"

# Every export target, and how to tell whether its credentials are saved. Auto-export is a
# *separate* opt-in per target (`auto_export_<target>`), so a user can save a token for a
# one-off manual export without it firing on every sync.
TARGETS = ("markdown", "obsidian", "flomo", "notion")


def _has_credentials(target: str, config_path: Path | None = None) -> bool:
    if target == "markdown":
        return bool(get_config(_MARKDOWN_DIR, config_path))
    if target == "obsidian":
        return bool(get_config(_OBSIDIAN_DIR, config_path))
    if target == "flomo":
        return bool(get_config(_FLOMO_WEBHOOK, config_path))
    return bool(get_config(_NOTION_TOKEN, config_path) and get_config(_NOTION_DATABASE, config_path))


def _auto_key(target: str) -> str:
    return f"auto_export_{target}"


def auto_enabled(target: str, config_path: Path | None = None) -> bool:
    return get_config(_auto_key(target), config_path) == "1"


def set_auto(target: str, on: bool, config_path: Path | None = None) -> None:
    """Turn auto-export for a target on or off (credentials are left untouched)."""
    save_config(_auto_key(target), "1" if on else "", config_path)


def saved_targets(config_path: Path | None = None) -> list[str]:
    """Targets whose credentials are saved, regardless of whether auto-export is on."""
    return [t for t in TARGETS if _has_credentials(t, config_path)]


def configured_targets(config_path: Path | None = None) -> list[str]:
    """Targets that a sync should auto-export to: credentials saved *and* auto-export on."""
    return [t for t in TARGETS if _has_credentials(t, config_path) and auto_enabled(t, config_path)]


def _record(conn: sqlite3.Connection, scope: str, started: int, status: str, detail: str) -> None:
    conn.execute(
        "INSERT INTO sync_runs(started_at, completed_at, status, scope, detail) VALUES (?, ?, ?, ?, ?)",
        (started, int(time.time()), status, scope, detail),
    )
    conn.commit()


def _watermark(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT max(sort) AS m FROM books WHERE total_notes > 0").fetchone()
    return int(row["m"] or 0)


def run_auto_exports(
    conn: sqlite3.Connection, report: Reporter = print, config_path: Path | None = None
) -> list[dict[str, object]]:
    """Export to every configured destination. Never raises: a failing target is recorded
    and reported, and the others still run. Returns one result dict per configured target."""
    results: list[dict[str, object]] = []
    for target in configured_targets(config_path):
        started = int(time.time())
        try:
            if target == "markdown":
                dest = Path(get_config(_MARKDOWN_DIR, config_path)).expanduser()
                count = export_markdown(conn, dest)
                detail = f"{count} 篇 → {dest}"
            elif target == "obsidian":
                dest = Path(get_config(_OBSIDIAN_DIR, config_path)).expanduser()
                res = export_obsidian(conn, dest)
                count = int(res)
                detail = f"新建 {res.created} 篇，追加 {res.appended} 篇，新增 {res.new_items} 条 → {dest}"
            elif target == "flomo":
                webhook = get_config(_FLOMO_WEBHOOK, config_path)
                since = int(get_state(conn, "export_flomo_sort") or 0)
                count = export_flomo(conn, webhook, since_sort=since)
                set_state(conn, "export_flomo_sort", str(_watermark(conn)))
                conn.commit()
                detail = f"{count} 条 memo（增量）"
            else:  # notion
                token = get_config(_NOTION_TOKEN, config_path)
                database = get_config(_NOTION_DATABASE, config_path)
                since = int(get_state(conn, "export_notion_sort") or 0)
                count = export_notion(conn, token, database, since_sort=since)
                set_state(conn, "export_notion_sort", str(_watermark(conn)))
                conn.commit()
                detail = f"{count} 页（增量）"
        except Exception as error:  # noqa: BLE001 — one bad target must not abort the rest
            _record(conn, f"export:{target}", started, "failed", str(error))
            report(f"自动导出 {target} 失败：{error}")
            results.append({"target": target, "status": "failed", "error": str(error)})
            continue
        _record(conn, f"export:{target}", started, "success", detail)
        report(f"自动导出 {target}：{detail}")
        results.append({"target": target, "status": "success", "count": count})
    return results
