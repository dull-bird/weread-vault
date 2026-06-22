from __future__ import annotations

import html
import json
import sqlite3
import threading
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .db import connect, summary


def _json(handler: BaseHTTPRequestHandler, body: object, status: int = 200) -> None:
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(encoded)


def _page() -> bytes:
    return """<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>WeRead Vault</title><style>
*{box-sizing:border-box}body{margin:0;background:#f6f7f9;color:#1c2430;font:15px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1000px;margin:0 auto;padding:36px 20px 64px}h1{margin:0;font-size:28px}.sub{color:#667085;margin:8px 0 28px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:28px}.card,section{background:white;border:1px solid #e7e9ee;border-radius:10px;padding:18px;box-shadow:0 1px 2px #1018280a}.card b{display:block;font-size:28px;margin-top:6px}section{margin-top:16px}h2{margin:0 0 14px;font-size:18px}form{display:flex;gap:8px}input{flex:1;border:1px solid #cbd2dd;border-radius:7px;padding:10px;font:inherit}button{border:0;border-radius:7px;background:#155eef;color:white;padding:10px 15px;font:inherit;cursor:pointer}table{border-collapse:collapse;width:100%;margin-top:12px}th,td{text-align:left;border-bottom:1px solid #eef0f3;padding:10px 6px;vertical-align:top}th{color:#667085;font-size:13px}td small{color:#667085}.empty{color:#667085;margin:8px 0}@media(max-width:620px){.cards{grid-template-columns:1fr}table{font-size:13px}.hide-mobile{display:none}}</style></head>
<body><main><h1>WeRead Vault</h1><p class='sub'>仅浏览本地 SQLite 数据；网页不会请求微信读书。</p>
<div class='cards'><div class='card'>书籍<b id='books'>—</b></div><div class='card'>划线<b id='highlights'>—</b></div><div class='card'>想法<b id='thoughts'>—</b></div></div>
<section><h2>搜索本地笔记</h2><form id='search'><input id='q' placeholder='输入关键词，搜索划线和想法'><button>搜索</button></form><div id='results' class='empty'>输入关键词后搜索。</div></section>
<section><h2>最近有笔记的书</h2><div id='book-list' class='empty'>加载中…</div></section></main>
<script>const e=x=>document.getElementById(x),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function load(){let s=await fetch('/api/summary').then(r=>r.json());for(let k of ['books','highlights','thoughts'])e(k).textContent=s[k]??0;let b=await fetch('/api/books?limit=20').then(r=>r.json());e('book-list').innerHTML=b.length?'<table><thead><tr><th>书名</th><th class="hide-mobile">作者</th><th>笔记</th><th>进度</th></tr></thead><tbody>'+b.map(x=>`<tr><td>${esc(x.title||'未命名')}</td><td class="hide-mobile">${esc(x.author||'—')}</td><td>${x.total_notes||0}</td><td>${x.reading_progress||0}%</td></tr>`).join('')+'</tbody></table>':'尚未同步数据。运行 <code>weread-vault sync</code>。'}
e('search').onsubmit=async ev=>{ev.preventDefault();let q=e('q').value.trim();if(!q)return;let rows=await fetch('/api/search?q='+encodeURIComponent(q)).then(r=>r.json());e('results').innerHTML=rows.length?'<table><tbody>'+rows.map(x=>`<tr><td><b>${esc(x.title||'未命名')}</b><br><small>${esc(x.kind)} · ${esc(x.chapter||'')}</small><br>${esc(x.content||'')}</td></tr>`).join('')+'</tbody></table>':'没有匹配结果。'};load();</script></body></html>""".encode("utf-8")


def make_handler(db_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return  # Book/note text must not end up in terminal logs.

        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)
            if parsed.path == "/":
                body = _page()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            with connect(db_path) as conn:
                if parsed.path == "/health":
                    _json(self, {"status": "ok"})
                elif parsed.path == "/api/summary":
                    _json(self, summary(conn))
                elif parsed.path == "/api/books":
                    limit = min(max(int(query.get("limit", [20])[0]), 1), 100)
                    rows = conn.execute(
                        "SELECT title,author,total_notes,reading_progress FROM books ORDER BY sort DESC LIMIT ?", (limit,)
                    ).fetchall()
                    _json(self, [dict(row) for row in rows])
                elif parsed.path == "/api/search":
                    term = query.get("q", [""])[0].strip()
                    if not term:
                        _json(self, [])
                        return
                    needle = f"%{term}%"
                    rows = conn.execute(
                        """SELECT * FROM (
                          SELECT b.title AS title,'划线' AS kind,h.chapter_title AS chapter,h.mark_text AS content,h.create_time AS created
                            FROM highlights h JOIN books b ON b.book_id=h.book_id WHERE h.mark_text LIKE ?
                          UNION ALL
                          SELECT b.title,'想法',t.chapter_name,t.content,t.create_time
                            FROM thoughts t JOIN books b ON b.book_id=t.book_id WHERE t.content LIKE ?
                        ) ORDER BY created DESC LIMIT 100""",
                        (needle, needle),
                    ).fetchall()
                    _json(self, [dict(row) for row in rows])
                else:
                    _json(self, {"error": "not found"}, 404)
    return Handler


def serve(db_path: Path, port: int, open_browser: bool = False) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(db_path))
    url = f"http://127.0.0.1:{port}/"
    print(f"本地预览：{url}")
    print("按 Ctrl+C 停止服务。")
    if open_browser:
        threading.Timer(0.2, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
    finally:
        server.server_close()
