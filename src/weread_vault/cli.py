from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

from .config import DEFAULT_PORT, default_db_path
from .db import connect, initialize, summary
from .errors import WereadVaultError
from .export import export_markdown
from .gateway import Gateway
from .sync import SyncService
from .web import serve


def _path(value: str | None) -> Path:
    return Path(value).expanduser() if value else default_db_path()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="weread-vault", description="本地优先的微信读书笔记库")
    result.add_argument("--db", help="SQLite 文件路径（默认：用户数据目录）")
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="创建本地 SQLite 数据库")
    sync = sub.add_parser("sync", help="从微信读书同步到本地库")
    sync.add_argument("scope", nargs="?", choices=("all", "books", "notes", "stats"), default="all")
    sync.add_argument("--full-notes", action="store_true", help="忽略变更水位，重新同步所有有笔记的书")
    sync.add_argument("--limit", type=int, help="最多同步多少本笔记书；适合首次测试或分批同步")
    sub.add_parser("status", help="显示本地库状态")
    export = sub.add_parser("export", help="导出本地笔记")
    export_sub = export.add_subparsers(dest="export_command", required=True)
    markdown = export_sub.add_parser("markdown", help="导出为 Markdown")
    markdown.add_argument("--out", required=True, help="目标目录")
    backup = sub.add_parser("backup", help="创建 SQLite 一致性备份")
    backup.add_argument("--out", required=True, help="备份文件路径")
    serve_parser = sub.add_parser("serve", help="打开本地网页预览")
    serve_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"端口（默认 {DEFAULT_PORT}）")
    serve_parser.add_argument("--open", action="store_true", help="自动在默认浏览器打开")
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
                if args.scope == "books":
                    count = service.books()
                elif args.scope == "notes":
                    count = service.notes(args.full_notes, args.limit)
                elif args.scope == "stats":
                    count = service.stats()
                else:
                    count = service.all(args.full_notes, args.limit)
            print(f"同步完成：{count}")
        elif args.command == "status":
            _print_status(db_path)
        elif args.command == "export":
            _require_db(db_path)
            with connect(db_path) as conn:
                count = export_markdown(conn, Path(args.out).expanduser())
            print(f"已导出 {count} 篇 Markdown")
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
    except (WereadVaultError, OSError, sqlite3.Error) as error:
        print(f"错误：{error}", file=sys.stderr)
        raise SystemExit(1) from error
