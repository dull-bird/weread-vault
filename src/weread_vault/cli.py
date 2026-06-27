from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import webbrowser
from pathlib import Path

from . import __version__
from .config import DEFAULT_PORT, default_db_path
from .db import connect, initialize, summary
from .errors import WereadVaultError
from .export import export_markdown
from .gateway import Gateway
from .integrations import export_flomo, export_notion
from .sync import SyncService
from .web import _reading_stats, serve, weread_url


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
                      choices=("all", "shelf", "books", "notes", "stats", "info", "popular"), default="all")
    sync.add_argument("--full-notes", action="store_true", help="忽略变更水位，重新同步所有有笔记的书")
    sync.add_argument("--refresh", action="store_true", help="sync info 专用：重抓所有书的富信息（含简介），不只补缺")
    sync.add_argument("--limit", type=int, help="最多同步多少本笔记书；适合首次测试或分批同步")
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
    flomo = export_sub.add_parser("flomo", help="导出到 flomo（每本书一条 memo）")
    flomo.add_argument("--webhook", help="flomo 专属 API；默认读环境变量 FLOMO_WEBHOOK")
    flomo.add_argument("--limit", type=int, help="最多导出多少本")
    notion = export_sub.add_parser("notion", help="导出到 Notion 数据库（每本书一页）")
    notion.add_argument("--token", help="Notion 集成 token；默认读 NOTION_TOKEN")
    notion.add_argument("--database", help="Notion 数据库 ID；默认读 NOTION_DATABASE_ID")
    notion.add_argument("--limit", type=int, help="最多导出多少本")
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
    return result


def _open_url(url: str) -> None:
    """Open a URL with the OS default handler. On macOS that routes weread.qq.com links to the
    WeRead app if it's installed (universal links), otherwise the browser; same idea elsewhere."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", url], check=False)
    elif system == "Windows":
        os.startfile(url)  # type: ignore[attr-defined]
    elif shutil.which("xdg-open"):
        subprocess.run(["xdg-open", url], check=False)
    else:
        webbrowser.open(url)


def _open_weread_app(book_id: str) -> bool:
    """Try to open the book in the native macOS WeRead app via its weread:// scheme. Returns True
    if the app handled it; False (e.g. app not installed → no handler) so the caller falls back."""
    if platform.system() != "Darwin":
        return False
    result = subprocess.run(["open", f"weread://bDetail?bId={book_id}"], capture_output=True, check=False)
    return result.returncode == 0


def _open_book(path: Path, query: str, *, pick: int | None = None, web: bool = False,
               print_only: bool = False) -> None:
    _require_db(path)
    query = query.strip()
    cols = "SELECT book_id,title,author,reading_progress,total_notes FROM books"
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
    web_url = weread_url(book_id)
    label = f"《{book['title']}》{book['author'] or ''}".rstrip()
    if print_only:
        link = web_url if web else (f"weread://bDetail?bId={book_id}" if platform.system() == "Darwin" else web_url)
        print(f"{label}\n{link}")
        return
    # On macOS, try the native app first; if it's not installed the open fails and we fall back to
    # the web page. With --web (or on other platforms) go straight to the web page — works anywhere.
    if not web and _open_weread_app(book_id):
        print(f"已在微信读书 App 打开 {label}")
        return
    if not web and platform.system() == "Darwin":
        print("未检测到微信读书 App，改用网页版。")
    _open_url(web_url)
    print(f"已在网页版打开 {label}\n{web_url}")


def _require_db(path: Path) -> None:
    if not path.exists():
        raise WereadVaultError(f"找不到本地数据库：{path}。先运行 weread-vault init 或 weread-vault sync。")


def _print_status(path: Path) -> None:
    _require_db(path)
    with connect(path) as conn:
        data = summary(conn)
        print(f"数据库：{path}")
        print(f"书籍：{data['books']} · 划线：{data['highlights']} · 想法：{data['thoughts']}")
        print(f"最近成功同步：{data['last_success'] or '从未'}")
        if data["last_failure"]:
            print(f"最近失败同步：{data['last_failure']}（失败的书不会推进同步水位）")


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
                    else:
                        count = service.all(args.full_notes, args.limit)
            if isinstance(count, dict):
                parts = [f"书架 {count['shelf']}", f"书目 {count['books']}",
                         f"笔记 {count['notes']}", f"统计 {count['stats']}"]
                if count.get("removed"):
                    parts.append(f"清理旧书 {count['removed']}")
                print("同步完成：" + "，".join(parts))
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
                info = scheduler.install(hour, minute, db=args.db, export=args.export)
                print(f"已设置每天 {hour:02d}:{minute:02d} 自动同步（{info['platform']}）。")
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
                for table in ("highlights", "thoughts", "reading_stats", "books", "sync_runs", "sync_state"):
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
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                    ):
                        schema[name] = [row["name"] for row in readonly.execute(f"PRAGMA table_info({name})")]
                    _emit_json({
                        "tables": schema,
                        "column_notes": {
                            "books": "一本书一行。rating=推荐值0–1000(/10得百分比)；word_count字数；total_notes笔记数；"
                                     "reading_progress 0–100；book_id 以 'MP_' 开头=公众号；category 形如 '经济理财-理财'。",
                            "highlights": "划线。mark_text=原文；create_time=Unix秒(用 datetime(create_time,'unixepoch','+8 hours') 转北京时间)；book_id 关联 books。",
                            "thoughts": "想法/书评。is_book_review=1为整本书评；content=内容；create_time=Unix秒。",
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
        elif args.command == "export":
            _require_db(db_path)
            with connect(db_path) as conn:
                if args.export_command == "markdown":
                    count = export_markdown(conn, Path(args.out).expanduser(), force=args.force,
                                            with_popular=args.with_popular)
                    print(f"已更新 {count} 篇 Markdown（无变化的已跳过）")
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
        elif args.command == "serve":
            initialize(db_path)
            if not 1 <= args.port <= 65535:
                raise WereadVaultError("端口必须在 1 到 65535 之间。")
            serve(db_path, args.port, args.open)
        elif args.command == "open":
            _open_book(db_path, args.query, pick=args.pick, web=args.web, print_only=args.print_only)
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
