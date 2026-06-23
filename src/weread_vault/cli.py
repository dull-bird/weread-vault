from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

from .config import DEFAULT_PORT, default_db_path
from .db import connect, initialize, summary
from .errors import WereadVaultError
from .export import export_markdown
from .gateway import Gateway
from .integrations import export_flomo, export_notion
from .sync import SyncService
from .web import _reading_stats, serve


def _path(value: str | None) -> Path:
    return Path(value).expanduser() if value else default_db_path()


def _emit_json(obj: object) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


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
    result.add_argument("--db", help="SQLite 文件路径（默认：用户数据目录）")
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="创建本地 SQLite 数据库")
    sync = sub.add_parser("sync", help="从微信读书同步到本地库")
    sync.add_argument("scope", nargs="?", choices=("all", "shelf", "books", "notes", "stats", "info"), default="all")
    sync.add_argument("--full-notes", action="store_true", help="忽略变更水位，重新同步所有有笔记的书")
    sync.add_argument("--limit", type=int, help="最多同步多少本笔记书；适合首次测试或分批同步")
    sub.add_parser("status", help="显示本地库状态")
    sub.add_parser("stats", help="输出阅读统计 JSON（供 AI 分析）")
    export = sub.add_parser("export", help="导出本地笔记")
    export_sub = export.add_subparsers(dest="export_command", required=True)
    markdown = export_sub.add_parser("markdown", help="导出为 Markdown")
    markdown.add_argument("--out", required=True, help="目标目录")
    markdown.add_argument("--force", action="store_true", help="忽略增量，强制重写所有文件")
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
    return result


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
            initialize(db_path)
            with connect(db_path) as conn:
                service = SyncService(conn, Gateway())
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
                    count = service.info(args.limit)
                else:
                    count = service.all(args.full_notes, args.limit)
            print(f"同步完成：{count}")
        elif args.command == "status":
            _print_status(db_path)
        elif args.command == "stats":
            _require_db(db_path)
            with connect(db_path) as conn:
                _emit_json(_reading_stats(conn))
        elif args.command == "export":
            _require_db(db_path)
            with connect(db_path) as conn:
                if args.export_command == "markdown":
                    count = export_markdown(conn, Path(args.out).expanduser(), force=args.force)
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
