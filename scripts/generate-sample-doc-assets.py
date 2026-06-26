#!/usr/bin/env python3
"""Generate privacy-safe docs screenshots from the real Web UI.

The script starts a temporary WeRead Vault web server backed by the deterministic
sample SQLite data, then captures the actual app UI with headless Chrome. Book
metadata comes from the sample seed; notes, thoughts, reading stats, progress,
and activity are generated demo data.

Run from the repository root:
  python3 scripts/generate-sample-doc-assets.py
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
SAMPLE_SQL = ROOT / "docs" / "sample-data" / "weread-vault-sample.sql"
# 详情页演示书：从示例库里真实存在的 book_id（划线最多、有想法和热门划线的那本）。
DETAIL_BOOK = "38260364"  # 《给教师的建议》
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import sqlite3  # noqa: E402

from weread_vault.web import make_handler  # noqa: E402


def build_sample_db(db_path: Path) -> None:
    """从提交在仓库里的示例 SQL（真实的 100 本精选书）重建一个 SQLite，用于截图。"""
    conn = sqlite3.connect(db_path)
    conn.executescript(SAMPLE_SQL.read_text(encoding="utf-8"))
    conn.close()


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


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(url: str) -> None:
    import urllib.request

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.15)
    raise RuntimeError(f"Timed out waiting for {url}")


def screenshot(chrome: str, url: str, output: Path, width: int, height: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--user-data-dir={profile}",
                f"--window-size={width},{height}",
                "--force-device-scale-factor=2",  # 2 倍像素密度，封面和文字不发糊
                "--virtual-time-budget=4000",  # 多给点时间等真实书封从 CDN 加载完
                f"--screenshot={output}",
                url,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main() -> None:
    chrome = chrome_binary()
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "weread-vault-sample.db"
        build_sample_db(db_path)
        port = free_port()
        server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(db_path))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{port}/"
        try:
            wait_for_server(base)
            b = f"?book={DETAIL_BOOK}"
            assets = {
                "dashboard.png": ("", 1440, 1040),
                "book-detail.png": (b, 1440, 1040),
                "detail-mine.png": (f"{b}&tab=mine", 1280, 980),
                "detail-popular.png": (f"{b}&tab=popular", 1280, 980),
                "detail-reviews.png": (f"{b}&tab=reviews", 1280, 980),
                "detail-similar.png": (f"{b}&tab=similar", 1280, 980),
                "popular-highlights.png": (f"{b}&tab=popular", 1440, 1040),
                "reading-stats.png": ("?view=stats&period=overall", 1440, 1040),
                "stats-all.png": ("?view=stats&period=overall", 1280, 1320),
                "stats-year.png": ("?view=stats&period=annually", 1280, 1320),
                "stats-month.png": ("?view=stats&period=monthly", 1280, 1320),
                "stats-heatmap.png": ("?view=stats&period=overall", 1280, 520),
            }
            for name, (query, width, height) in assets.items():
                screenshot(chrome, base + query, OUT / name, width, height)
                print(f"wrote {OUT / name}")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    main()
