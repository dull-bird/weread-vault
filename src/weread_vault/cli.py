from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from . import __version__
from .config import DEFAULT_PORT, default_db_path
from .db import connect, initialize, summary
from .errors import WereadVaultError
from .export import export_markdown, export_obsidian
from .gateway import Gateway
from .integrations import export_flomo, export_notion
from .paper import format_dry_run, import_paper_books, parse_paper_notes
from .review import run_review
from .sync import SyncService
from .web import _reading_stats, serve


def _path(value: str | None) -> Path:
    return Path(value).expanduser() if value else default_db_path()


def _emit_json(obj: object) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


_RELEASES_API = "https://api.github.com/repos/dull-bird/weread-vault/releases/latest"


def _curl(args: list[str]) -> bytes:
    try:
        return subprocess.check_output(["curl", "-fsSL", *args], stderr=subprocess.STDOUT, timeout=30)
    except FileNotFoundError as error:
        raise WereadVaultError("当前 Python 不支持 HTTPS，且找不到 curl；请用带 SSL 的 Python 运行，或安装 curl。") from error
    except subprocess.CalledProcessError as error:
        detail = error.output.decode("utf-8", "replace").strip()
        raise WereadVaultError(f"curl 请求失败：{detail or error}") from error
    except subprocess.TimeoutExpired as error:
        raise WereadVaultError("curl 请求超时。") from error


def _fetch_json(url: str) -> dict[str, object]:
    import urllib.error
    import urllib.request

    request = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json", "User-Agent": "weread-vault"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            print("还没有发布版本（仓库尚无 Release）。")
            return {}
        raise WereadVaultError(f"检查更新失败：{error}") from error
    except urllib.error.URLError as error:
        if "unknown url type: https" not in str(error):
            raise WereadVaultError(f"检查更新失败：{error}") from error
        # Some self-managed Python builds omit _ssl. urllib then has no HTTPS
        # handler at all. Fall back to curl when available so `update` remains
        # usable from that environment.
        return json.loads(_curl(["-H", "Accept: application/vnd.github+json", "-H", "User-Agent: weread-vault", url]).decode("utf-8"))
    except Exception as error:  # noqa: BLE001 — network/JSON, surfaced as a friendly message
        raise WereadVaultError(f"检查更新失败：{error}") from error


def _download(url: str, output: str) -> None:
    import urllib.error
    import urllib.request

    try:
        urllib.request.urlretrieve(url, output)
    except urllib.error.URLError as error:
        if "unknown url type: https" not in str(error):
            raise WereadVaultError(f"下载安装包失败：{error}") from error
        _curl(["-o", output, url])


def _version_tuple(value: str) -> tuple[int, ...]:
    import re
    return tuple(int(part) for part in re.findall(r"\d+", value)) or (0,)


def _check_update(download: bool = False) -> None:
    import platform

    data = _fetch_json(_RELEASES_API)
    if not data:
        return
    latest = (data.get("tag_name") or "").lstrip("v")
    if not latest:
        print("还没有发布版本。")
        return
    if _version_tuple(latest) <= _version_tuple(__version__):
        print(f"已是最新版本（当前 {__version__}，最新 {latest}）。")
        return
    print(f"发现新版本 {latest}（当前 {__version__}）。")
    system = platform.system().lower()
    key = "macos" if system == "darwin" else "windows" if system.startswith("win") else "linux"
    assets = data.get("assets") or []
    if key == "windows":
        asset = next((a for a in assets if (a.get("name") or "").lower() == "weread-vault-windows-setup.exe"), None)
        asset = asset or next((a for a in assets if "setup" in (a.get("name") or "").lower()), None)
        asset = asset or next((a for a in assets if (a.get("name") or "").lower() == "weread-vault.exe"), None)
        asset = asset or next((a for a in assets if (a.get("name") or "").lower().endswith(".exe")), None)
    elif key == "macos":
        asset = next((a for a in assets if (a.get("name") or "").lower().endswith(".dmg")), None)
        asset = asset or next((a for a in assets if "macos" in (a.get("name") or "").lower()), None)
    else:
        asset = next((a for a in assets if "linux" in (a.get("name") or "").lower()), None)
    if asset and download:
        _download(asset["browser_download_url"], asset["name"])
        print(f"已下载安装包：{asset['name']}")
    elif asset:
        print(f"下载（{key}）：{asset['browser_download_url']}")
        print("或重新运行：weread-vault update --download")
    else:
        print(f"发布页：{data.get('html_url')}")


def _parse_kv(items: list[str]) -> dict[str, object]:
    # Coerce purely-numeric values to int so params like count=5 are sent as numbers,
    # but keep id-like fields and keywords as strings (e.g. bookId=635722 must stay a string).
    keep_str = {"keyword", "sid", "sessionid", "synckey_str"}
    params: dict[str, object] = {}
    for item in items:
        if "=" not in item:
            raise WereadVaultError(f"参数需为 key=value 形式：{item}")
        key, value = item.split("=", 1)
        if value.lstrip("-").isdigit() and not key.lower().endswith("id") and key.lower() not in keep_str:
            params[key] = int(value)
        else:
            params[key] = value
    return params


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="weread-vault", description="本地优先的微信读书笔记库")
    result.add_argument("--version", action="version", version=f"weread-vault {__version__}")
    result.add_argument("--db", help="SQLite 文件路径（默认：用户数据目录）")
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="创建本地 SQLite 数据库")
    sync = sub.add_parser("sync", help="从微信读书同步到本地库")
    sync.add_argument("scope", nargs="?",
                      choices=("all", "shelf", "books", "notes", "stats", "info", "popular", "progress"), default="all")
    sync.add_argument("--full-notes", action="store_true", help="忽略变更水位，重新同步所有有笔记的书")
    sync.add_argument("--refresh", action="store_true", help="sync info 专用：重抓所有书的富信息（含简介），不只补缺")
    sync.add_argument("--limit", type=int, help="最多同步多少本笔记书；适合首次测试或分批同步")
    sync.add_argument("--progress-limit", dest="progress_limit", type=int, default=150,
                      help="每次最多同步多少本书的阅读进度（默认 150，0=不取）")
    sync.add_argument("--no-export", dest="no_export", action="store_true",
                      help="本次同步后不触发已配置的自动导出（Obsidian/flomo/Notion）")
    sub.add_parser("status", help="显示本地库状态")
    reset = sub.add_parser("reset", help="清空本机阅读数据（换账号前用；不影响 API Key）")
    reset.add_argument("--yes", action="store_true", help="跳过确认直接清空")
    update = sub.add_parser("update", help="检查是否有新版本（GitHub Release）")
    update.add_argument("--download", action="store_true", help="下载对应平台的安装包到当前目录")
    schedule_p = sub.add_parser("schedule", help="设置/取消每天自动同步（用系统定时器，不常驻）")
    schedule_p.add_argument("--daily", metavar="HH:MM", help="每天几点自动同步，如 07:00")
    schedule_p.add_argument("--export", metavar="DIR", help="同步成功后顺带导出 Markdown 到该目录")
    schedule_p.add_argument("--off", action="store_true", help="取消自动同步")
    schedule_p.add_argument("--status", action="store_true", help="查看当前自动同步设置")
    sub.add_parser("stats", help="输出阅读统计 JSON（供 AI 分析）")
    query = sub.add_parser("query", help="对本地库执行只读 SQL（供 AI 灵活分析）")
    query.add_argument("sql", nargs="?", help="SELECT / WITH 语句；省略则等同 --schema")
    query.add_argument("--schema", action="store_true", help="打印所有表与列，便于 AI 写查询")
    query.add_argument("--limit", type=int, default=500, help="最多返回行数（默认 500）")
    export = sub.add_parser("export", help="导出本地笔记")
    export_sub = export.add_subparsers(dest="export_command", required=True)
    markdown = export_sub.add_parser("markdown", help="导出为 Markdown")
    markdown.add_argument("--out", required=True, help="目标目录")
    markdown.add_argument("--force", action="store_true", help="忽略增量，强制重写所有文件")
    markdown.add_argument("--with-popular", action="store_true",
                          help="合并导出他人热门划线（需先 weread-vault sync popular）")
    obsidian = export_sub.add_parser("obsidian", help="增量导出到 Obsidian（保留手写内容与管理区块）")
    obsidian.add_argument("--out", required=True, help="目标目录")
    obsidian.add_argument("--with-popular", action="store_true",
                          help="合并导出他人热门划线（需先 weread-vault sync popular）")
    flomo = export_sub.add_parser("flomo", help="导出到 flomo（每本书一条 memo）")
    flomo.add_argument("--webhook", help="flomo 专属 API；默认读环境变量 FLOMO_WEBHOOK")
    flomo.add_argument("--limit", type=int, help="最多导出多少本")
    notion = export_sub.add_parser("notion", help="导出到 Notion 数据库（每本书一页）")
    notion.add_argument("--token", help="Notion 集成 token；默认读 NOTION_TOKEN")
    notion.add_argument("--database", help="Notion 数据库 ID；默认读 NOTION_DATABASE_ID")
    notion.add_argument("--limit", type=int, help="最多导出多少本")
    export_cfg = export_sub.add_parser(
        "config", help="配置自动导出目的地（每次同步后自动导出到已配置的目的地）")
    export_cfg.add_argument("--markdown", metavar="DIR", help="设置 Markdown/Obsidian 导出目录")
    export_cfg.add_argument("--obsidian", metavar="DIR", help="设置 Obsidian 增量导出目录")
    export_cfg.add_argument("--flomo", metavar="WEBHOOK", help="设置 flomo 专属 API")
    export_cfg.add_argument("--notion-token", dest="notion_token", metavar="TOKEN", help="设置 Notion 集成 token")
    export_cfg.add_argument("--notion-db", dest="notion_db", metavar="ID", help="设置 Notion 数据库 ID")
    export_cfg.add_argument("--enable", choices=("markdown", "obsidian", "flomo", "notion"),
                            help="开启某个目的地的自动导出（凭据不变）")
    export_cfg.add_argument("--disable", choices=("markdown", "obsidian", "flomo", "notion"),
                            help="关闭某个目的地的自动导出（保留凭据，仍可手动导出）")
    export_cfg.add_argument("--clear", choices=("markdown", "obsidian", "flomo", "notion"), help="清除某个目的地的配置（含凭据与自动开关）")
    export_cfg.add_argument("--show", action="store_true", help="查看已配置的自动导出目的地（密钥打码）")
    log_p = sub.add_parser("log", help="查看同步/导出历史（读取 sync_runs）")
    log_p.add_argument("--limit", type=int, default=20, help="最多显示多少条（默认 20）")
    log_p.add_argument("--json", dest="as_json", action="store_true", help="输出 JSON（供 AI 读取）")
    backup = sub.add_parser("backup", help="创建 SQLite 一致性备份")
    backup.add_argument("--out", required=True, help="备份文件路径")
    serve_parser = sub.add_parser("serve", help="打开本地网页预览")
    serve_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"端口（默认 {DEFAULT_PORT}）")
    serve_parser.add_argument("--open", action="store_true", help="自动在默认浏览器打开")

    # —— 微信读书 API 直连命令（面向 AI agent；输出 JSON 到 stdout，需 WEREAD_API_KEY）——
    sub.add_parser("apis", help="列出微信读书 Skill 支持的全部接口")
    api_p = sub.add_parser("api", help="直接调用任意微信读书接口（高级/Agent）")
    api_p.add_argument("endpoint", help="接口路径，如 /store/search、/book/bestbookmarks")
    api_p.add_argument("params", nargs="*", help="key=value 参数，如 keyword=三体 count=5")
    search_p = sub.add_parser("search", help="搜索微信读书书城（书籍/作者/全文等）")
    search_p.add_argument("keyword", help="搜索关键词")
    search_p.add_argument("--scope", type=int, help="搜索范围 tab（不传为默认 tab）")
    search_p.add_argument("--count", type=int, default=10, help="返回数量（默认 10）")
    book_p = sub.add_parser("book", help="查看某本书的扩展数据（含他人热门划线/公开书评）")
    book_p.add_argument("book_id", help="书籍 ID")
    book_p.add_argument(
        "aspect",
        choices=("info", "chapters", "popular", "reviews", "progress"),
        help="info=书籍信息 chapters=目录 popular=他人热门划线 reviews=公开书评 progress=我的进度",
    )
    book_p.add_argument("--count", type=int, default=20, help="reviews 的返回数量（默认 20）")
    open_p = sub.add_parser("open", help="在微信读书打开一本书（按书名搜本地库，开 App / 网页版）")
    open_p.add_argument("query", help="书名关键词（模糊匹配本地书架）或 book_id（精确）")
    open_p.add_argument("--pick", type=int, metavar="N", help="多本匹配时，打开列表里的第 N 本")
    open_p.add_argument("--web", action="store_true", help="强制用浏览器打开网页版（默认在 macOS 上尝试唤起 App）")
    open_p.add_argument("--print", dest="print_only", action="store_true", help="只打印链接，不打开")
    paper_p = sub.add_parser("import-paper", help="导入纸质书笔记（纯文本/Markdown 文件或 stdin）")
    paper_p.add_argument("files", nargs="*", metavar="FILE", help="纸质书笔记文件（省略或 - 读 stdin）")
    paper_p.add_argument("--dry-run", dest="dry_run", action="store_true", help="只解析并打印结果，不写入数据库")
    rev_p = sub.add_parser("review", help="间隔重复每日回顾（从划线和想法中抽取）")
    rev_p.add_argument("-n", "--count", dest="count", type=int, default=5, help="抽取条数（默认 5）")
    rev_p.add_argument("--append", metavar="FILE", help="将回顾 Markdown 追加到指定文件末尾（不存在则创建）")
    rev_p.add_argument("--dry-run", dest="dry_run", action="store_true", help="只展示，不更新 review_log")
    rev_p.add_argument("--seed", type=int, help="随机种子（用于可复现抽取）")
    rev_p.add_argument("--book", metavar="KEYWORD", help="只从书名或 book_id 匹配的书里抽取")
    return result


def _open_book(path: Path, query: str, *, pick: int | None = None, web: bool = False,
               print_only: bool = False) -> None:
    _require_db(path)
    query = query.strip()
    cols = "SELECT book_id,title,author,reading_progress,total_notes,reader_link,deep_link FROM books"
    with connect(path) as conn:
        # Exact book_id first (an agent often already has the id from `query`/`book`), else title.
        by_id = conn.execute(f"{cols} WHERE book_id=?", (query,)).fetchone()
        if by_id is not None:
            rows = [by_id]
        else:
            rows = conn.execute(
                f"{cols} WHERE title LIKE ? ORDER BY (title=?) DESC, total_notes DESC, sort DESC LIMIT 20",
                (f"%{query}%", query),
            ).fetchall()
    if not rows:
        raise WereadVaultError(f"本地书架没找到匹配「{query}」的书（书名或 book_id）。先 weread-vault sync，或换个关键词。")
    exact = [row for row in rows if row["title"] == query]
    if pick is not None:
        if not 1 <= pick <= len(rows):
            raise WereadVaultError(f"--pick 超出范围：匹配到 {len(rows)} 本，请选 1–{len(rows)}。")
        book = rows[pick - 1]
    elif len(rows) == 1:
        book = rows[0]
    elif len(exact) == 1:
        book = exact[0]  # the query is itself a full, unambiguous title
    else:
        # Ambiguous — don't guess. List the matches so the user (or the AI) can pick.
        print(f"「{query}」匹配到 {len(rows)} 本，用 --pick N 选一本，或直接用 book_id 打开：")
        for index, row in enumerate(rows, 1):
            progress = f"{row['reading_progress']}%" if row["reading_progress"] is not None else "—"
            print(f"  [{index}] {row['title']}（{row['author'] or '—'}）· 进度 {progress} · "
                  f"{row['total_notes'] or 0} 笔记 · id={row['book_id']}")
        return
    book_id = book["book_id"]
    label = f"《{book['title']}》{book['author'] or ''}".rstrip()
    link = book["reader_link"] or book["deep_link"]
    if not link:
        try:
            info = Gateway().call("/book/info", bookId=book_id)
        except Exception:  # noqa: BLE001
            info = {}
        r_link = (info.get("readerLink") or "").strip() or None
        d_link = (info.get("deepLink") or "").strip() or None
        if r_link or d_link:
            with connect(path) as conn:
                conn.execute(
                    """UPDATE books SET reader_link=COALESCE(?,reader_link),
                    deep_link=COALESCE(?,deep_link) WHERE book_id=?""",
                    (r_link, d_link, book_id),
                )
            link = r_link or d_link
    if not link:
        raise WereadVaultError(f"官方没有给这本书的链接：{label}")
    if print_only or platform.system() != "Darwin":
        print(f"{label}\n{link}")
        return
    subprocess.run(["open", link], check=False)
    print(f"已打开 {label}\n{link}")


def _require_db(path: Path) -> None:
    if not path.exists():
        raise WereadVaultError(f"找不到本地数据库：{path}。先运行 weread-vault init 或 weread-vault sync。")
    # Bring an existing database up to the current schema (idempotent: adds new columns/views only).
    initialize(path)


def _fmt_sync_time(value: int | str | None) -> str:
    if not value:
        return "从未"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(int(value)))


def _print_status(path: Path) -> None:
    _require_db(path)
    with connect(path) as conn:
        data = summary(conn)
        print(f"数据库：{path}")
        print(
            f"书籍：{data['books']} · 纸质书 {data['paper_books']} 本 · "
            f"划线：{data['highlights']} · 想法：{data['thoughts']}"
        )
        print(f"最近成功同步：{_fmt_sync_time(data['last_success'])}")
        if data["last_failure"]:
            print(f"最近失败同步：{_fmt_sync_time(data['last_failure'])}（失败的书不会推进同步水位）")


def _mask(secret: str) -> str:
    """Show only the tail of a secret so a user can recognise it without exposing it."""
    if not secret:
        return "—"
    return f"…{secret[-4:]}" if len(secret) > 4 else "已设置"


def _export_config(args: argparse.Namespace) -> None:
    """Save / clear / show the auto-export destinations used after each sync."""
    from .config import get_config, save_config
    from .autoexport import auto_enabled, configured_targets, set_auto

    changed = False
    # Setting a destination's credentials via the CLI implies you want it auto-exported.
    if args.markdown:
        save_config("export_markdown_dir", str(Path(args.markdown).expanduser()))
        set_auto("markdown", True)
        changed = True
    if args.obsidian:
        save_config("export_obsidian_dir", str(Path(args.obsidian).expanduser()))
        set_auto("obsidian", True)
        changed = True
    if args.flomo:
        save_config("flomo_webhook", args.flomo)
        set_auto("flomo", True)
        changed = True
    if args.notion_token or args.notion_db:
        if args.notion_token:
            save_config("notion_token", args.notion_token)
        if args.notion_db:
            save_config("notion_database", args.notion_db)
        set_auto("notion", True)
        changed = True
    if args.enable:
        set_auto(args.enable, True)
        print(f"已开启 {args.enable} 的同步后自动导出。")
        changed = True
    if args.disable:
        set_auto(args.disable, False)
        print(f"已关闭 {args.disable} 的自动导出（凭据保留，仍可手动导出）。")
        changed = True
    if args.clear:
        if args.clear == "markdown":
            save_config("export_markdown_dir", "")
        elif args.clear == "obsidian":
            save_config("export_obsidian_dir", "")
        elif args.clear == "flomo":
            save_config("flomo_webhook", "")
        else:
            save_config("notion_token", "")
            save_config("notion_database", "")
        set_auto(args.clear, False)
        print(f"已清除 {args.clear} 导出配置。")
        changed = True

    if changed and not args.show:
        targets = configured_targets()
        print("已保存。" + (f"同步后将自动导出到：{'、'.join(targets)}。" if targets else "当前没有开启自动导出的目的地。"))
        return

    # Default (or --show): report what is configured, secrets masked.
    md = get_config("export_markdown_dir")
    obs = get_config("export_obsidian_dir")
    flomo = get_config("flomo_webhook")
    token = get_config("notion_token")
    database = get_config("notion_database")

    def _line(label: str, value: str, target: str) -> str:
        state = "自动" if auto_enabled(target) else ("仅手动" if value else "—")
        return f"  {label}：{value or '未配置'}  [{state}]"

    print("导出配置（[自动]=每次完整 sync 后触发；[仅手动]=已存凭据但不自动导出）：")
    print(_line("Markdown/Obsidian", md, "markdown"))
    print(_line("Obsidian（增量）", obs, "obsidian"))
    print(_line("flomo", _mask(flomo) if flomo else "", "flomo"))
    notion_val = ("token " + _mask(token) + " · db " + _mask(database)) if (token and database) else ""
    print(_line("Notion", notion_val, "notion"))
    targets = configured_targets()
    print(f"  → 自动导出目的地：{'、'.join(targets) if targets else '（无）'}")


def _print_log(path: Path, limit: int, as_json: bool) -> None:
    import datetime as _dt

    with connect(path) as conn:
        rows = conn.execute(
            """SELECT started_at, completed_at, status, scope, detail
            FROM sync_runs ORDER BY id DESC LIMIT ?""",
            (max(1, limit),),
        ).fetchall()
    if as_json:
        _emit_json([dict(row) for row in rows])
        return
    if not rows:
        print("还没有同步/导出记录。")
        return
    icon = {"success": "✓", "failed": "✗", "running": "…", "interrupted": "⚠"}
    for row in rows:
        when = _dt.datetime.fromtimestamp(row["started_at"]).strftime("%m-%d %H:%M")
        secs = (row["completed_at"] - row["started_at"]) if row["completed_at"] else None
        dur = f"{secs}s" if secs is not None else "—"
        mark = icon.get(row["status"], "·")
        detail = f" — {row['detail']}" if row["detail"] else ""
        print(f"{mark} {when}  {row['scope']:<14} {dur:>5}{detail}")


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    db_path = _path(args.db)
    try:
        if args.command == "init":
            initialize(db_path)
            print(f"已创建本地数据库：{db_path}")
        elif args.command == "sync":
            from . import sync_lock
            initialize(db_path)
            # One sync at a time across processes, so a scheduled job and an OpenClaw cron both
            # firing at 07:00 don't collide on the database — the second simply skips.
            with sync_lock.single_sync(db_path) as acquired:
                if not acquired:
                    print("已有一个同步正在进行，本次跳过。")
                    return
                with connect(db_path) as conn:
                    service = SyncService(conn, Gateway())
                    warning = service.account_warning()
                    if warning:
                        print(f"⚠️  {warning}", file=sys.stderr)
                    if args.limit is not None and args.limit < 1:
                        raise WereadVaultError("--limit 必须是正整数。")
                    if args.progress_limit < 0:
                        raise WereadVaultError("--progress-limit 不能为负数。")
                    if args.scope == "shelf":
                        count = service.shelf()
                    elif args.scope == "books":
                        count = service.books()
                    elif args.scope == "notes":
                        count = service.notes(args.full_notes, args.limit)
                    elif args.scope == "stats":
                        count = service.stats()
                    elif args.scope == "info":
                        count = service.info(args.limit, args.refresh)
                    elif args.scope == "popular":
                        count = service.popular(args.limit, args.refresh)
                    elif args.scope == "progress":
                        count = service.progress(args.limit if args.limit is not None else args.progress_limit)
                    else:
                        count = service.all(args.full_notes, args.limit, progress_limit=args.progress_limit)
                    # A full sync fans out to every configured export destination while the
                    # sync lock and connection are still held, so a daily job keeps Obsidian/
                    # flomo/Notion current with no extra scheduling. Only the full `all` scope
                    # triggers it; partial scopes (shelf/notes/…) don't.
                    if args.scope == "all" and not args.no_export:
                        from .autoexport import run_auto_exports
                        run_auto_exports(conn)
            bd = getattr(service, "_shelf_breakdown", None)
            if isinstance(count, dict):
                if bd:
                    detail = f"电子书 {bd['books']}，有声书 {bd['albums']}" + (
                        f"，文章收藏 {bd['mp']}" if bd["mp"] else ""
                    )
                    shelf_label = f"书架 {count['shelf']}（{detail}）"
                else:
                    shelf_label = f"书架 {count['shelf']}"
                parts = [shelf_label, f"书目 {count['books']}",
                         f"笔记 {count['notes']}", f"统计 {count['stats']}"]
                if count.get("progress"):
                    parts.append(f"进度 {count['progress']}")
                if count.get("popular"):
                    parts.append(f"热门划线 {count['popular']}")
                if count.get("removed"):
                    parts.append(f"清理旧书 {count['removed']}")
                print("同步完成：" + "，".join(parts))
            elif args.scope == "shelf" and bd:
                detail = f"电子书 {bd['books']}，有声书 {bd['albums']}" + (
                    f"，文章收藏 {bd['mp']}" if bd["mp"] else ""
                )
                print(f"同步完成：书架 {count}（{detail}）")
            else:
                print(f"同步完成：{count}")
        elif args.command == "status":
            _print_status(db_path)
        elif args.command == "update":
            _check_update(download=args.download)
        elif args.command == "schedule":
            from . import schedule as scheduler
            from .config import api_key_source
            if args.off:
                print("已取消每天自动同步。" if scheduler.remove() else "本来就没有设置自动同步。")
            elif args.status:
                _emit_json(scheduler.status())
            elif args.daily:
                hour, minute = scheduler.parse_time(args.daily)
                if args.export:
                    # Route --export through the auto-export config so the scheduled job is a
                    # plain `sync` that fans out to every configured destination, not just this dir.
                    from .config import save_config
                    from .autoexport import set_auto
                    save_config("export_markdown_dir", str(Path(args.export).expanduser()))
                    set_auto("markdown", True)
                info = scheduler.install(hour, minute, db=args.db)
                print(f"已设置每天 {hour:02d}:{minute:02d} 自动同步（{info['platform']}）。")
                from .autoexport import configured_targets
                targets = configured_targets()
                if targets:
                    print(f"同步后将自动导出到：{'、'.join(targets)}。")
                if api_key_source() == "env":
                    print("⚠️  你的 API Key 只在当前终端环境变量里——定时任务读不到。"
                          "请先用网页「同步设置」保存 Key 到本机配置，或 weread-vault 同步一次以保存。", file=sys.stderr)
            else:
                raise WereadVaultError("用法：schedule --daily HH:MM [--export 目录] / --off / --status")
        elif args.command == "reset":
            _require_db(db_path)
            if not args.yes:
                print("将清空本地全部阅读数据（书目/划线/想法/统计/同步状态），不影响 API Key。"
                      "确认请重跑：weread-vault reset --yes", file=sys.stderr)
                raise SystemExit(1)
            with connect(db_path) as conn:
                for table in ("highlights", "thoughts", "reading_stats", "obsidian_exported", "review_log", "books", "sync_runs", "sync_state"):
                    conn.execute(f"DELETE FROM {table}")
                conn.commit()
            print("已清空本地阅读数据。")
        elif args.command == "stats":
            _require_db(db_path)
            with connect(db_path) as conn:
                _emit_json(_reading_stats(conn))
        elif args.command == "query":
            _require_db(db_path)
            # Open read-only so any write attempt fails at the SQLite level, not just by our check.
            readonly = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            readonly.row_factory = sqlite3.Row
            try:
                if args.schema or not args.sql:
                    schema = {}
                    for (name,) in readonly.execute(
                        "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' ORDER BY name"
                    ):
                        schema[name] = [row["name"] for row in readonly.execute(f"PRAGMA table_info({name})")]
                    _emit_json({
                        "tables": schema,
                        "column_notes": {
                            "books": "一本书一行。rating=推荐值0–1000(/10得百分比)；word_count字数；total_notes笔记数；"
                                     "progress/reading_progress 0–100；reading_seconds阅读秒数；finish_time读完时间；"
                                     "read_update_time最近阅读时间；reader_link/deep_link=官方跳转链接；"
                                     "book_id 以 'MP_' 开头=公众号；category 形如 '经济理财-理财'。",
                            "book_status": "阅读状态视图。status='已读'(finished=1 或 progress=100) / '在读'(progress 1–99) / '未读'(其他)；"
                                           "含 book_id,title,author,progress,reading_seconds,finish_time,read_update_time,status。",
                            "highlights": "划线。mark_text=原文；create_time=Unix秒(用 datetime(create_time,'unixepoch','+8 hours') 转北京时间)；book_id 关联 books。",
                            "thoughts": "想法/书评。is_book_review=1为整本书评；content=想法内容；abstract=对应的划线原文；chapter_idx=章节序号；create_time=Unix秒。",
                            "reading_stats": "统计快照(JSON 在 payload)；解析好的统计请改用 `weread-vault stats`。",
                        },
                        "examples": [
                            "SELECT title, rating FROM books WHERE rating>0 ORDER BY rating DESC LIMIT 10",
                            "SELECT category, count(*) n FROM books WHERE book_id NOT LIKE 'MP_%' GROUP BY category ORDER BY n DESC",
                            "SELECT b.title, count(*) c FROM highlights h JOIN books b ON b.book_id=h.book_id GROUP BY h.book_id ORDER BY c DESC LIMIT 10",
                            "SELECT strftime('%Y',datetime(create_time,'unixepoch','+8 hours')) y, count(*) FROM highlights GROUP BY y",
                        ],
                    })
                else:
                    sql = args.sql.strip().rstrip(";")
                    if not sql.lower().startswith(("select", "with")):
                        raise WereadVaultError("只允许只读查询（SELECT / WITH 开头）。")
                    rows = readonly.execute(sql).fetchmany(max(1, args.limit))
                    _emit_json([dict(row) for row in rows])
            finally:
                readonly.close()
        elif args.command == "export" and args.export_command == "config":
            _export_config(args)
        elif args.command == "export":
            _require_db(db_path)
            with connect(db_path) as conn:
                if args.export_command == "markdown":
                    count = export_markdown(conn, Path(args.out).expanduser(), force=args.force,
                                            with_popular=args.with_popular)
                    print(f"已更新 {count} 篇 Markdown（无变化的已跳过）")
                elif args.export_command == "obsidian":
                    res = export_obsidian(conn, Path(args.out).expanduser(), with_popular=args.with_popular)
                    print(f"新建 {res.created} 篇，追加 {res.appended} 篇，新增 {res.new_items} 条")
                elif args.export_command == "flomo":
                    webhook = args.webhook or os.environ.get("FLOMO_WEBHOOK")
                    if not webhook:
                        raise WereadVaultError("需要 flomo webhook：--webhook 或环境变量 FLOMO_WEBHOOK。")
                    count = export_flomo(conn, webhook, args.limit)
                    print(f"已发送 {count} 条 memo 到 flomo。")
                elif args.export_command == "notion":
                    token = args.token or os.environ.get("NOTION_TOKEN")
                    database = args.database or os.environ.get("NOTION_DATABASE_ID")
                    if not token or not database:
                        raise WereadVaultError(
                            "需要 Notion --token 与 --database（或环境变量 NOTION_TOKEN / NOTION_DATABASE_ID）。"
                        )
                    count = export_notion(conn, token, database, args.limit)
                    print(f"已在 Notion 创建 {count} 页。")
        elif args.command == "backup":
            _require_db(db_path)
            destination = Path(args.out).expanduser()
            destination.parent.mkdir(parents=True, exist_ok=True)
            with connect(db_path) as source, sqlite3.connect(destination) as target:
                source.backup(target)
            print(f"备份已创建：{destination}")
        elif args.command == "log":
            _require_db(db_path)
            _print_log(db_path, args.limit, args.as_json)
        elif args.command == "serve":
            initialize(db_path)
            if not 1 <= args.port <= 65535:
                raise WereadVaultError("端口必须在 1 到 65535 之间。")
            serve(db_path, args.port, args.open)
        elif args.command == "open":
            _open_book(db_path, args.query, pick=args.pick, web=args.web, print_only=args.print_only)
        elif args.command == "import-paper":
            chunks: list[str] = []
            files = args.files or ["-"]
            for f in files:
                if f == "-":
                    chunks.append(sys.stdin.read())
                else:
                    chunks.append(Path(f).expanduser().read_text(encoding="utf-8"))
            parsed = parse_paper_notes("\n\n".join(chunks))
            if args.dry_run:
                print(format_dry_run(parsed))
                return
            initialize(db_path)
            with connect(db_path) as conn:
                counts = import_paper_books(conn, parsed)
            print(f"已导入纸质书 {counts['books']} 本：划线 {counts['highlights']} 条，想法 {counts['thoughts']} 条。")
        elif args.command == "review":
            _require_db(db_path)
            append_file = Path(args.append).expanduser() if args.append else None
            with connect(db_path) as conn:
                md = run_review(
                    conn,
                    n=args.count,
                    append_path=append_file,
                    dry_run=args.dry_run,
                    seed=args.seed,
                    book=args.book,
                )
            if append_file is None:
                print(md)
        elif args.command == "apis":
            for api in Gateway().call("/_list").get("apis", []):
                required = "，".join(p["name"] for p in api.get("params", []) if p.get("required"))
                suffix = f"（必填：{required}）" if required else ""
                print(f"{api['api_name']}  — {api.get('description', '')}{suffix}")
        elif args.command == "api":
            _emit_json(Gateway().call(args.endpoint, **_parse_kv(args.params)))
        elif args.command == "search":
            params: dict[str, object] = {"keyword": args.keyword, "count": args.count}
            if args.scope is not None:
                params["scope"] = args.scope
            _emit_json(Gateway().call("/store/search", **params))
        elif args.command == "book":
            endpoint = {
                "info": "/book/info",
                "chapters": "/book/chapterinfo",
                "popular": "/book/bestbookmarks",
                "reviews": "/review/list",
                "progress": "/book/getprogress",
            }[args.aspect]
            call_params: dict[str, object] = {"bookId": args.book_id}
            if args.aspect == "reviews":
                call_params["count"] = args.count
            _emit_json(Gateway().call(endpoint, **call_params))
    except (WereadVaultError, OSError, sqlite3.Error) as error:
        print(f"错误：{error}", file=sys.stderr)
        raise SystemExit(1) from error
