from __future__ import annotations

import hashlib
import html
import json
import sqlite3
import threading
import time
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .config import api_key_source, default_config_path, save_api_key
from .db import connect, summary
from .gateway import Gateway
from .sync import SyncService


def _json(handler: BaseHTTPRequestHandler, body: object, status: int = 200) -> None:
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(encoded)


def _read_json_body(handler: BaseHTTPRequestHandler, limit: int = 4096) -> dict[str, object]:
    length = min(int(handler.headers.get("Content-Length", "0")), limit)
    if not length:
        return {}
    body = json.loads(handler.rfile.read(length).decode("utf-8"))
    return body if isinstance(body, dict) else {}


def _sync_counts(service: SyncService, mode: str) -> dict[str, int]:
    if mode == "books":
        return {"books": service.books(), "notes": 0, "stats": 0}
    if mode == "notes":
        return {"books": service.books(), "notes": service.notes(), "stats": service.stats()}
    if mode == "full":
        return {"books": service.books(), "notes": service.notes(full=True), "stats": service.stats()}
    raise ValueError("未知同步模式。")


def weread_url(book_id: str) -> str:
    """WeRead web book-detail URL. Reproduces WeRead's published bookId→hash transform."""
    book_id = str(book_id)
    digest = hashlib.md5(book_id.encode("utf-8")).hexdigest()
    result = digest[:3]
    if book_id.isdigit():
        parts = [format(int(book_id[i:i + 9]), "x") for i in range(0, len(book_id), 9)]
        type_flag = "3"
    else:
        parts = ["".join(format(ord(char), "x") for char in book_id)]
        type_flag = "4"
    result += type_flag + "2" + digest[-2:]
    for index, part in enumerate(parts):
        length = format(len(part), "x")
        result += (length if len(length) == 2 else "0" + length) + part
        if index < len(parts) - 1:
            result += "g"
    if len(result) < 20:
        result += digest[: 20 - len(result)]
    result += hashlib.md5(result.encode("utf-8")).hexdigest()[:3]
    return "https://weread.qq.com/web/bookDetail/" + result


def _session_distribution(conn: sqlite3.Connection, gap: int = 1800) -> dict[str, object]:
    """Infer reading sessions from highlight timestamps: a gap over `gap` seconds starts a new
    session; a session's span (first→last highlight) approximates its length. This is a proxy —
    pure reading without highlights is invisible — but it reveals fragmented vs. long-form reading.
    """
    times = [row[0] for row in conn.execute(
        "SELECT create_time FROM highlights WHERE create_time IS NOT NULL ORDER BY create_time"
    )]
    spans: list[int] = []
    if times:
        start = previous = times[0]
        for current in times[1:]:
            if current - previous > gap:
                spans.append(previous - start)
                start = current
            previous = current
        spans.append(previous - start)
    buckets = [("≤5 分钟", 0, 300), ("5–15 分钟", 300, 900), ("15–30 分钟", 900, 1800),
               ("30–60 分钟", 1800, 3600), (">60 分钟", 3600, float("inf"))]
    distribution = [{"label": label, "count": sum(1 for s in spans if lo <= s < hi)} for label, lo, hi in buckets]
    return {"total": len(spans), "distribution": distribution}


def _reading_stats(conn: sqlite3.Connection) -> dict[str, object]:
    rows = conn.execute(
        """SELECT mode, payload FROM reading_stats
        WHERE (mode, fetched_at) IN (SELECT mode, MAX(fetched_at) FROM reading_stats GROUP BY mode)"""
    ).fetchall()
    by_mode = {row["mode"]: json.loads(row["payload"]) for row in rows}
    overall = by_mode.get("overall") or {}
    if not overall:
        return {"hasData": False}
    # WeRead's yearly buckets are Asia/Shanghai (UTC+8) year boundaries; shift before reading the year.
    by_year = sorted(
        ({"label": time.gmtime(int(ts) + 8 * 3600).tm_year, "seconds": secs} for ts, secs in (overall.get("readTimes") or {}).items()),
        key=lambda item: item["label"],
    )
    categories = [
        {"title": c.get("categoryTitle"), "seconds": c.get("readingTime", 0), "count": c.get("readingCount", 0)}
        for c in (overall.get("preferCategory") or [])
    ][:8]
    authors = [
        {"name": a.get("name"), "count": a.get("count", 0), "readTime": a.get("readTime", "")}
        for a in (overall.get("preferAuthor") or [])
    ][:8]
    longest = [
        {"title": (item.get("book") or {}).get("title"), "readSeconds": item.get("readTime", 0)}
        for item in (overall.get("readLongest") or [])
    ][:10]
    periods = {
        mode: {"totalReadTime": by_mode[mode].get("totalReadTime", 0), "readDays": by_mode[mode].get("readDays", 0)}
        for mode in ("weekly", "monthly", "annually")
        if mode in by_mode
    }
    return {
        "hasData": True,
        "sessions": _session_distribution(conn),
        "overall": {
            "totalReadTime": overall.get("totalReadTime", 0),
            "readDays": overall.get("readDays", 0),
            "authorCount": overall.get("authorCount", 0),
            "readStat": overall.get("readStat", []),
            "preferTime": overall.get("preferTime", []),
            "byYear": by_year,
            "categories": categories,
            "authors": authors,
            "longest": longest,
            "preferCategoryWord": overall.get("preferCategoryWord", ""),
            "preferTimeWord": overall.get("preferTimeWord", ""),
        },
        "periods": periods,
    }


def _page() -> bytes:
    return r"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>WeRead Vault</title><style>
:root{--bg:#fafbfc;--fg:#10151c;--muted:#6b7480;--line:#e9ebef;--card:#fff;--brand:#155eef;--brand2:#7c3aed;--shadow:0 1px 2px #10182808,0 4px 16px #10182808}
@media(prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#8b949e;--line:#222831;--card:#161b22;--shadow:0 1px 2px #0006}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased}
main{max-width:1080px;margin:0 auto;padding:40px 22px 72px}
.layout{display:flex;max-width:1200px;margin:0 auto;min-height:100vh}
.sidebar{width:208px;flex:0 0 208px;padding:24px 14px;border-right:1px solid var(--line);position:sticky;top:0;height:100vh;display:flex;flex-direction:column;gap:4px}
.brand{font-size:18px;font-weight:700;letter-spacing:-.02em;padding:0 10px}.brand .dot{color:var(--brand)}
.tagline{font-size:11px;color:var(--muted);padding:4px 10px 16px;line-height:1.4}
.nav{display:flex;flex-direction:column;gap:3px}
.nav button{text-align:left;background:transparent;color:var(--fg);border:0;padding:10px 12px;border-radius:9px;font:inherit;font-size:14px;cursor:pointer;font-weight:500}
.nav button:hover{background:color-mix(in srgb,var(--brand) 8%,transparent)}
.nav button.on{background:color-mix(in srgb,var(--brand) 13%,transparent);color:var(--brand);font-weight:600}
.ic{width:16px;height:16px;display:inline-block;vertical-align:-3px;flex:0 0 auto}
.nav button{display:flex;align-items:center}.nav button .ic{margin-right:10px;width:17px;height:17px}
.cp{display:inline-flex;align-items:center;justify-content:center}.cp .ic{width:15px;height:15px;vertical-align:0}
.wr{display:inline-flex;align-items:center}.wr .ic{width:13px;height:13px;margin-right:5px;vertical-align:0}
.side-foot{margin-top:auto;padding:10px;font-size:12px;border-top:1px solid var(--line)}
.content{flex:1;min-width:0;max-width:1000px;padding:30px 32px 72px}
.content h2:first-child{margin-top:0}
.view[hidden]{display:none}
@media(max-width:720px){.layout{flex-direction:column}.sidebar{width:auto;height:auto;position:static;flex-direction:row;flex-wrap:wrap;align-items:center;gap:8px;border-right:0;border-bottom:1px solid var(--line);padding:14px}.tagline{display:none}.nav{flex-direction:row;flex-wrap:wrap}.nav button{padding:7px 10px;font-size:13px}.side-foot{margin:0;border:0;padding:0}.content{padding:20px}}
.head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
h1{margin:0;font-size:27px;letter-spacing:-.02em;font-weight:700}.dot{color:var(--brand)}
.sub{color:var(--muted);margin:9px 0 30px;font-size:14px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:34px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;box-shadow:var(--shadow);position:relative;overflow:hidden}
.card .k{color:var(--muted);font-size:13px;font-weight:500}.card b{display:block;font-size:30px;font-weight:700;margin-top:4px;letter-spacing:-.02em}
.card::after{content:'';position:absolute;right:-20px;top:-20px;width:72px;height:72px;border-radius:50%;background:radial-gradient(circle,var(--brand) 0%,transparent 70%);opacity:.10}
section{margin-top:30px}h2{margin:0 0 16px;font-size:16px;font-weight:650;display:flex;align-items:center;gap:8px}h2 .n{color:var(--muted);font-weight:500;font-size:13px}
form{display:flex;gap:8px}input{flex:1;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:11px 13px;font:inherit;color:var(--fg)}input:focus{outline:2px solid var(--brand);outline-offset:-1px;border-color:transparent}
button{border:0;border-radius:10px;background:var(--brand);color:#fff;padding:11px 18px;font:inherit;font-weight:550;cursor:pointer}button:hover{filter:brightness(1.08)}
button:disabled{cursor:not-allowed;opacity:.62;filter:none}.actions{display:flex;align-items:center;gap:10px;margin:-10px 0 26px;flex-wrap:wrap}.hint{color:var(--muted);font-size:13px}.msg{font-size:13px}.msg.ok{color:#059669}.msg.err{color:#dc2626}.keybox{display:none;align-items:center;gap:8px;flex-wrap:wrap;width:100%}.keybox input{max-width:380px}.ghost{background:transparent;color:var(--brand);border:1px solid color-mix(in srgb,var(--brand) 35%,var(--line))}
.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:18px}
.toolbar select{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:8px 11px;font:inherit;font-size:13px;color:var(--fg);cursor:pointer}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:9px;overflow:hidden}
.seg button{background:var(--card);color:var(--muted);border:0;padding:8px 14px;font:inherit;font-size:13px;cursor:pointer}
.seg button.on{background:var(--brand);color:#fff}
.stats-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
@media(max-width:620px){.stats-grid{grid-template-columns:1fr}}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow)}
.panel h3{margin:0 0 12px;font-size:13px;font-weight:600;color:var(--muted)}
.chart{width:100%;height:auto;display:block;overflow:visible}
.caxis{fill:var(--muted);font-size:9px}
.big{display:flex;gap:26px;flex-wrap:wrap;align-items:baseline}
.big .v{font-size:27px;font-weight:700;letter-spacing:-.02em}.big .l{font-size:12px;color:var(--muted)}
.hbar{display:flex;align-items:center;gap:10px;margin:8px 0;font-size:13px}
.hbar .nm{width:92px;flex:0 0 92px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--fg)}
.hbar .tk{flex:1;height:9px;border-radius:5px;background:var(--line);overflow:hidden}.hbar .tk i{display:block;height:100%;background:linear-gradient(90deg,var(--brand),var(--brand2))}
.hbar .vv{width:70px;flex:0 0 70px;text-align:right;font-size:12px;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:20px 16px}
@media(max-width:860px){.grid{grid-template-columns:repeat(4,1fr)}}
.list{display:flex;flex-direction:column;gap:8px}
.lrow{display:flex;align-items:center;gap:14px;background:var(--card);border:1px solid var(--line);border-radius:11px;padding:10px 14px;cursor:pointer;box-shadow:var(--shadow)}
.lrow:hover{border-color:color-mix(in srgb,var(--brand) 40%,var(--line))}
.lrow .lc{width:38px;height:52px;flex:0 0 38px;border-radius:5px;overflow:hidden;position:relative;box-shadow:0 1px 3px #0003;background:var(--line)}
.lrow .lc .ph{font-size:8px;padding:3px}.lrow .lc img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.lrow .li{flex:1;min-width:0}.lrow .lt{font-size:14px;font-weight:550;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.lrow .la{font-size:12px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lrow .lcat{font-size:11px;color:var(--muted);background:var(--bg);border:1px solid var(--line);border-radius:999px;padding:3px 10px;white-space:nowrap}
.lrow .lp{width:110px;flex:0 0 110px}.lrow .ln{width:62px;text-align:right;font-size:12px;color:var(--muted);flex:0 0 62px}
@media(max-width:620px){.lrow .lcat,.lrow .lp{display:none}}
.book{display:flex;flex-direction:column;gap:9px;cursor:default}
.cover{aspect-ratio:3/4;border-radius:9px;overflow:hidden;box-shadow:0 2px 6px #1018281f,0 8px 20px #10182814;background:var(--line);position:relative;transition:transform .25s,box-shadow .25s}
.book:hover .cover{transform:translateY(-3px);box-shadow:0 4px 10px #10182824,0 14px 30px #1018281f}
.cover img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;background:var(--line)}
.ph{width:100%;height:100%;display:flex;align-items:center;justify-content:center;text-align:center;padding:12px;color:#fff;font-weight:650;font-size:14px;line-height:1.35}
.meta .t{font-size:13px;font-weight:550;line-height:1.35;height:2.7em;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.meta .a{font-size:12px;color:var(--muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar{height:4px;border-radius:3px;background:var(--line);margin-top:7px;overflow:hidden}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--brand),var(--brand2))}
.pc{font-size:11px;color:var(--muted);margin-top:4px;display:flex;justify-content:space-between}
.res{margin-top:6px}.row{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:13px 15px;margin-top:10px;box-shadow:var(--shadow)}
.row .h{font-size:12px;color:var(--muted);margin-bottom:5px}.row .h b{color:var(--fg)}.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:6px;background:color-mix(in srgb,var(--brand) 14%,transparent);color:var(--brand);margin-right:6px}
.empty{color:var(--muted);margin:8px 0;font-size:14px}
.book{cursor:pointer}
.prog{display:none;height:6px;border-radius:4px;background:var(--line);overflow:hidden;margin:2px 0 24px}
.prog.show{display:block}
.prog i{display:block;height:100%;width:0;border-radius:4px;background:linear-gradient(90deg,var(--brand),var(--brand2));transition:width .3s ease}
.prog.indet i{width:38%;animation:indet 1.15s ease-in-out infinite}
@keyframes indet{0%{margin-left:-38%}100%{margin-left:100%}}
.pager{display:flex;align-items:center;justify-content:center;gap:14px;margin-top:18px;color:var(--muted);font-size:13px}
.pager button{background:var(--card);color:var(--fg);border:1px solid var(--line);padding:7px 14px;font-weight:550}.pager button:disabled{opacity:.45}
.date{font-size:11px;color:var(--muted)}
.modal{position:fixed;inset:0;background:#0b0f17b3;backdrop-filter:blur(3px);display:none;z-index:50;overflow:auto}
.modal.show{display:block}
.sheet{max-width:760px;margin:40px auto;background:var(--bg);border:1px solid var(--line);border-radius:16px;box-shadow:0 20px 60px #0007;overflow:hidden}
.bh{display:flex;gap:18px;padding:24px;background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:2}
.bh .cover{width:84px;flex:0 0 84px}
.bh .bi{flex:1;min-width:0}.bh h3{margin:0 0 4px;font-size:19px;letter-spacing:-.01em}.bh .a{color:var(--muted);font-size:13px}
.bh .st{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}
.bkintro{margin-top:10px;font-size:12.5px;color:var(--muted);line-height:1.55;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;cursor:pointer}
.bkintro.open{-webkit-line-clamp:unset}.chip{font-size:12px;color:var(--muted);background:var(--bg);border:1px solid var(--line);border-radius:999px;padding:3px 10px}
.bh .x{align-self:flex-start;background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:9px;width:34px;height:34px;font-size:18px;line-height:1;padding:0;cursor:pointer}
.bhtools{display:flex;gap:8px;padding:14px 24px;border-bottom:1px solid var(--line);background:var(--card)}.bhtools button{padding:8px 14px;font-size:13px}
.notes{padding:8px 24px 36px}
.ch{margin:26px 0 10px;font-size:14px;font-weight:650;color:var(--brand);padding-bottom:7px;border-bottom:1px dashed var(--line)}
.hl{margin:14px 0;padding:12px 14px;border-left:3px solid var(--brand);background:var(--card);border-radius:0 10px 10px 0}
.hl[data-c='1']{border-color:#e11d48}.hl[data-c='2']{border-color:#ea580c}.hl[data-c='3']{border-color:#16a34a}.hl[data-c='4']{border-color:#2563eb}.hl[data-c='5']{border-color:#9333ea}
.hl .tx{font-size:14.5px;line-height:1.65}.hl .ft{margin-top:7px;display:flex;justify-content:flex-end}
.th{margin:14px 0;padding:13px 15px;background:color-mix(in srgb,var(--brand) 7%,var(--card));border:1px solid color-mix(in srgb,var(--brand) 22%,var(--line));border-radius:11px}
.th .lb{font-size:11px;font-weight:600;color:var(--brand);margin-bottom:6px}.th .tx{font-size:14px;line-height:1.6}.th .ft{margin-top:7px;display:flex;justify-content:flex-end}
.note-empty{padding:40px 24px;text-align:center;color:var(--muted)}
.tabs{display:flex;gap:18px;padding:12px 24px 0;background:var(--card);border-bottom:1px solid var(--line)}
.tabs button{background:transparent;border:0;border-bottom:2px solid transparent;color:var(--muted);padding:8px 2px;font:inherit;font-size:13px;cursor:pointer}
.tabs button.on{color:var(--brand);border-bottom-color:var(--brand);font-weight:600}
.pop{margin:12px 0;padding:11px 14px;background:var(--card);border:1px solid var(--line);border-radius:10px;border-left:3px solid var(--brand2)}
.pop .tx{font-size:14px;line-height:1.62}.pop .ft{margin-top:6px;font-size:12px;color:var(--muted);display:flex;justify-content:space-between;gap:10px}
.rv{margin:12px 0;padding:13px 15px;background:var(--card);border:1px solid var(--line);border-radius:11px}
.rv .au{font-size:12px;color:var(--muted);margin-bottom:6px;display:flex;justify-content:space-between;gap:10px}.rv .tx{font-size:14px;line-height:1.62}.rv .ft{margin-top:7px;display:flex;justify-content:flex-end}
.cp{background:transparent;border:0;color:var(--muted);font-size:12px;cursor:pointer;padding:2px 8px;border-radius:6px;flex:0 0 auto}
.cp:hover{background:color-mix(in srgb,var(--brand) 14%,transparent);color:var(--brand)}
.bhx{display:flex;align-items:center;gap:8px;align-self:flex-start}
.wr{font-size:12px;color:var(--brand);text-decoration:none;border:1px solid color-mix(in srgb,var(--brand) 35%,var(--line));border-radius:8px;padding:6px 10px;white-space:nowrap}.wr:hover{background:color-mix(in srgb,var(--brand) 10%,transparent)}
.smode{display:inline-flex;border:1px solid var(--line);border-radius:9px;overflow:hidden;vertical-align:middle}
.smode button{background:var(--card);border:0;color:var(--muted);padding:6px 12px;font:inherit;font-size:12px;cursor:pointer}.smode button.on{background:var(--brand);color:#fff}
@media(max-width:620px){.cards{grid-template-columns:1fr}.grid{grid-template-columns:repeat(3,1fr);gap:16px 12px}.sheet{margin:0;border-radius:0;min-height:100vh}}
</style></head>
<body><div class='layout'>
<aside class='sidebar'>
<div class='brand'>WeRead <span class='dot'>Vault</span></div>
<div class='tagline'>为 AI 工具打造的微信读书笔记库</div>
<nav class='nav'>
<button data-view='shelf' class='on' type='button'>书架</button>
<button data-view='stats' type='button'>阅读统计</button>
<button data-view='search' type='button'>搜索 / 书城</button>
<button data-view='sync' type='button'>同步设置</button>
</nav>
<div class='side-foot'><span id='api-key-status' class='hint'>检查 API Key…</span></div>
</aside>
<main class='content'>
<section class='view' data-view='shelf'>
<div class='cards'>
<div class='card'><span class='k'>书籍</span><b id='books'>—</b></div>
<div class='card'><span class='k'>划线</span><b id='highlights'>—</b></div>
<div class='card'><span class='k'>想法</span><b id='thoughts'>—</b></div></div>
<h2>书架 <span class='n' id='shelf-n'></span></h2>
<div class='toolbar'>
<div class='seg' id='view-seg'><button data-v='grid' class='on' type='button'>封面</button><button data-v='list' type='button'>列表</button></div>
<select id='sort-sel' title='排序'><option value='recent'>最近添加</option><option value='progress'>阅读进度</option><option value='notes'>笔记最多</option><option value='rating'>评分</option><option value='words'>字数</option><option value='title'>书名</option></select>
<select id='cat-sel' title='分类'><option value=''>全部分类</option></select>
</div>
<div id='shelf' class='empty'>加载中…</div><div id='shelf-pager'></div>
</section>
<section class='view' data-view='stats' hidden><h2>阅读统计 <span class='n' id='stats-word'></span></h2><div id='stats' class='empty'>加载中…</div></section>
<section class='view' data-view='search' hidden><h2>搜索 <span class='smode' id='smode'><button data-m='notes' class='on' type='button'>本地笔记</button><button data-m='store' type='button'>书城</button></span></h2><form id='search'><input id='q' placeholder='输入关键词，搜索划线和想法'><button>搜索</button></form><div id='results' class='res empty'>输入关键词后搜索。</div></section>
<section class='view' data-view='sync' hidden><h2>同步设置</h2>
<div class='actions'><button id='sync-btn' type='button'>同步</button><button id='full-btn' class='ghost' type='button'>完整重扫</button><span id='sync-msg' class='msg'></span><div id='keybox' class='keybox'><input id='api-key' type='password' autocomplete='off' placeholder='粘贴 WEREAD_API_KEY，仅保存到本机私有配置'><button id='save-key' class='ghost' type='button'>保存 API Key</button></div></div>
<div id='prog' class='prog'><i></i></div>
<p class='sub'>「同步」会先拉取全书架，再增量同步有变更的笔记，并追加阅读统计。首次可能较慢。API Key 仅保存到本机私有配置，不会上传。</p>
</section>
</main></div>
<div id='modal' class='modal'><div class='sheet' id='sheet'></div></div>
<script>
const e=x=>document.getElementById(x),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const SVG=p=>`<svg class=ic viewBox='0 0 24 24' fill=none stroke=currentColor stroke-width=2 stroke-linecap=round stroke-linejoin=round>${p}</svg>`;
const ICO={book:SVG("<path d='M4 19.5A2.5 2.5 0 0 1 6.5 17H20'/><path d='M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z'/>"),
 stats:SVG("<line x1=12 y1=20 x2=12 y2=10/><line x1=18 y1=20 x2=18 y2=4/><line x1=6 y1=20 x2=6 y2=16/>"),
 search:SVG("<circle cx=11 cy=11 r=8/><line x1=21 y1=21 x2=16.65 y2=16.65/>"),
 sync:SVG("<polyline points='23 4 23 10 17 10'/><polyline points='1 20 1 14 7 14'/><path d='M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15'/>"),
 copy:SVG("<rect x=9 y=9 width=13 height=13 rx=2 ry=2/><path d='M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1'/>"),
 ext:SVG("<path d='M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6'/><polyline points='15 3 21 3 21 9'/><line x1=10 y1=14 x2=21 y2=3/>")};
const PAL=[['#155eef','#7c3aed'],['#0891b2','#0e7490'],['#db2777','#9d174d'],['#ea580c','#b45309'],['#059669','#047857'],['#4f46e5','#7c3aed'],['#dc2626','#991b1b'],['#0d9488','#115e59']];
function hue(s){let h=0;for(let i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))>>>0;return PAL[h%PAL.length]}
function cover(x){const t=x.title||'未命名',fallback=ph(t);if(x.cover){return fallback+`<img loading=lazy src="${esc(x.cover)}" alt="${esc(t)}" onerror="this.remove()">`}return fallback}
function ph(t){const[a,b]=hue(t);return `<div class=ph style="background:linear-gradient(150deg,${a},${b})">${esc(t).slice(0,18)}</div>`}
let allBooks=[],curView='grid',curSort='recent',curCat='',shelfPage=1;const SHELF_PAGE=24;
const topCat=c=>c?String(c).split('-')[0]:'未分类';
const isMp=x=>String(x.book_id||'').startsWith('MP_');
const SORTERS={recent:(a,b)=>(b.sort||0)-(a.sort||0),progress:(a,b)=>(b.reading_progress||0)-(a.reading_progress||0),notes:(a,b)=>(b.total_notes||0)-(a.total_notes||0),rating:(a,b)=>(b.rating||0)-(a.rating||0),words:(a,b)=>(b.word_count||0)-(a.word_count||0),title:(a,b)=>String(a.title||'').localeCompare(String(b.title||''),'zh')};
function renderShelf(){
 const sh=e('shelf'),pg=e('shelf-pager');pg.innerHTML='';
 if(!allBooks.length){sh.className='empty';sh.innerHTML='尚未同步数据。点上方“同步”按钮拉取你的书架。';e('shelf-n').textContent='';return}
 let arr=allBooks.filter(x=>{if(curCat==='__mp__')return isMp(x);if(isMp(x))return false;return !curCat||topCat(x.category)===curCat}).slice().sort(SORTERS[curSort]||SORTERS.recent);
 if(!arr.length){sh.className='empty';sh.innerHTML='该分类下没有书。';e('shelf-n').textContent='共 0 本';return}
 const pages=Math.max(1,Math.ceil(arr.length/SHELF_PAGE));
 if(shelfPage>pages)shelfPage=pages;if(shelfPage<1)shelfPage=1;
 const slice=arr.slice((shelfPage-1)*SHELF_PAGE,shelfPage*SHELF_PAGE);
 e('shelf-n').textContent=`共 ${arr.length} 本`+(curCat?` · ${curCat}`:'')+(pages>1?` · 第 ${shelfPage}/${pages} 页`:'');
 if(curView==='list'){
  sh.className='list';
  sh.innerHTML=slice.map(x=>{const p=Math.max(0,Math.min(100,x.reading_progress||0));return `<div class=lrow onclick="openBook('${esc(x.book_id)}')"><div class=lc>${cover(x)}</div><div class=li><div class=lt>${esc(x.title||'未命名')}</div><div class=la>${esc(x.author||'—')}</div></div><span class=lcat>${esc(topCat(x.category))}</span><span class=ln>${x.rating?`推荐 ${(x.rating/10).toFixed(0)}%`:''}</span><div class=lp><div class=bar><i style="width:${p}%"></i></div></div><span class=ln>${x.total_notes||0} 笔记</span></div>`}).join('');
 }else{
  sh.className='grid';
  sh.innerHTML=slice.map(x=>{const p=Math.max(0,Math.min(100,x.reading_progress||0));return `<div class=book onclick="openBook('${esc(x.book_id)}')"><div class=cover>${cover(x)}</div><div class=meta><div class=t>${esc(x.title||'未命名')}</div><div class=a>${esc(x.author||'—')}</div></div><div class=bar><i style="width:${p}%"></i></div><div class=pc><span>${x.total_notes||0} 条笔记</span><span>${p}%</span></div></div>`}).join('');
 }
 if(pages>1){pg.innerHTML=`<div class=pager><button id=sprev type=button ${shelfPage<=1?'disabled':''}>上一页</button><span>第 ${shelfPage} / ${pages} 页 · 共 ${arr.length} 本</span><button id=snext type=button ${shelfPage>=pages?'disabled':''}>下一页</button></div>`;e('sprev').onclick=()=>{shelfPage--;renderShelf()};e('snext').onclick=()=>{shelfPage++;renderShelf();document.querySelector('.toolbar').scrollIntoView({behavior:'smooth',block:'start'})}}
}
async function load(){
 let s=await fetch('/api/summary').then(r=>r.json());for(let k of ['books','highlights','thoughts'])e(k).textContent=(s[k]??0).toLocaleString();
 allBooks=await fetch('/api/books?limit=5000').then(r=>r.json());
 const cats=[...new Set(allBooks.filter(x=>!isMp(x)).map(x=>topCat(x.category)))].sort((a,b)=>a.localeCompare(b,'zh'));
 const mpCount=allBooks.filter(isMp).length;
 e('cat-sel').innerHTML='<option value="">全部分类（不含公众号）</option>'+cats.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join('')+(mpCount?`<option value="__mp__">📰 公众号 (${mpCount})</option>`:'');
 if(![...e('cat-sel').options].some(o=>o.value===curCat))curCat='';
 e('cat-sel').value=curCat;
 renderShelf();
}
e('sort-sel').onchange=ev=>{curSort=ev.target.value;shelfPage=1;renderShelf()};
e('cat-sel').onchange=ev=>{curCat=ev.target.value;shelfPage=1;renderShelf()};
e('view-seg').querySelectorAll('button').forEach(b=>b.onclick=()=>{curView=b.dataset.v;shelfPage=1;e('view-seg').querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));renderShelf()});
async function loadSettings(){let x=await fetch('/api/settings').then(r=>r.json()),box=e('keybox'),status=e('api-key-status');box.style.display=x.source==='none'?'flex':'none';if(x.source==='env'){status.textContent='API Key 已由环境变量 WEREAD_API_KEY 设置。'}else if(x.source==='config'){status.textContent='API Key 已保存到本机私有配置。'}else{status.textContent='未设置 API Key。同步前请设置；会默认保存到本机私有配置。'}}
e('save-key').onclick=async()=>{const key=e('api-key').value.trim(),msg=e('sync-msg');if(!key){msg.className='msg err';msg.textContent='API Key 不能为空。';return}e('save-key').disabled=true;try{let res=await fetch('/api/settings/api-key',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:key})});let body=await res.json();if(!res.ok)throw new Error(body.error||'保存失败');e('api-key').value='';msg.className='msg ok';msg.textContent='API Key 已保存到本机私有配置。';await loadSettings()}catch(err){msg.className='msg err';msg.textContent=err.message||String(err)}finally{e('save-key').disabled=false}};
async function runSync(mode){const sbtn=e('sync-btn'),fbtn=e('full-btn'),msg=e('sync-msg'),prog=e('prog'),bar=prog.querySelector('i'),slabel=sbtn.textContent,flabel=fbtn.textContent;
 sbtn.disabled=fbtn.disabled=true;(mode==='full'?fbtn:sbtn).textContent='同步中…';
 msg.className='msg';msg.textContent='首次同步可能较慢，正在连接微信读书…';prog.className='prog show indet';bar.style.width='';
 let result=null;
 try{
  const res=await fetch('/api/sync/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode})});
  if(!res.ok){let b=await res.json().catch(()=>({}));throw new Error(b.error||('HTTP '+res.status))}
  const reader=res.body.getReader(),dec=new TextDecoder();let buf='';
  for(;;){const{value,done}=await reader.read();if(done)break;buf+=dec.decode(value,{stream:true});let nl;
   while((nl=buf.indexOf('\n'))>=0){const line=buf.slice(0,nl).trim();buf=buf.slice(nl+1);if(!line)continue;let o;try{o=JSON.parse(line)}catch(_){continue}
    if(o.error)throw new Error(o.error);
    if(o.done){result=o.counts;continue}
    if(o.line){msg.textContent=o.line;const m=o.line.match(/\[(\d+)\/(\d+)\]/);if(m&&+m[2]>0){prog.className='prog show';bar.style.width=Math.round(m[1]/m[2]*100)+'%'}}}}
  prog.className='prog show';bar.style.width='100%';
  msg.className='msg ok';msg.textContent=`同步完成：全书架 ${result?.shelf??0} 本，有笔记 ${result?.books??0} 本，更新笔记 ${result?.notes??0} 本，统计 +${result?.stats??0}`;
  await load();await loadSettings();
 }catch(err){msg.className='msg err';msg.textContent=err.message||String(err)}
 finally{sbtn.disabled=fbtn.disabled=false;sbtn.textContent=slabel;fbtn.textContent=flabel;setTimeout(()=>{e('prog').className='prog'},1000)}}
e('sync-btn').onclick=()=>runSync('sync');
e('full-btn').onclick=()=>runSync('full');
function fmtDate(ts){if(!ts)return '';const d=new Date(ts*1000);if(isNaN(d))return '';const p=n=>String(n).padStart(2,'0');return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`}
let curQ='',curPage=1;
async function doSearch(page){const q=curQ;if(!q)return;const res=e('results');
 // 仅首次搜索显示“搜索中…”；翻页时保留旧结果直接替换，避免高度塌缩造成的闪烁
 if(!res.querySelector('.row')){res.className='res empty';res.textContent='搜索中…'}
 let d=await fetch(`/api/search?q=${encodeURIComponent(q)}&page=${page}`).then(r=>r.json());curPage=d.page;
 if(!d.rows.length){res.className='res';res.innerHTML='<div class="res empty">没有匹配结果。</div>';return}
 const pages=Math.max(1,Math.ceil(d.total/d.page_size));
 const html=d.rows.map(x=>`<div class=row onclick="openBook('${esc(x.book_id)}')" style=cursor:pointer><div class=h><span class=tag>${esc(x.kind)}</span><b>${esc(x.title||'未命名')}</b> · ${esc(x.chapter||'')}<span style=float:right class=date>${fmtDate(x.created)}</span></div>${esc(x.content||'')}</div>`).join('')+`<div class=pager><button id=prev type=button ${d.page<=1?'disabled':''}>上一页</button><span>第 ${d.page} / ${pages} 页 · 共 ${d.total} 条</span><button id=next type=button ${d.page>=pages?'disabled':''}>下一页</button></div>`;
 res.className='res';res.innerHTML=html;
 e('prev')&&(e('prev').onclick=()=>doSearch(curPage-1));e('next')&&(e('next').onclick=()=>doSearch(curPage+1));}
let searchMode='notes',storeBooks=[];
async function doStoreSearch(){const q=curQ,res=e('results');res.className='res empty';res.textContent='搜索书城中…';
 const d=await fetch('/api/store-search?q='+encodeURIComponent(q)).then(r=>r.json());
 if(d.error){res.className='res';res.innerHTML=`<div class="res empty">${esc(d.error)}</div>`;return}
 storeBooks=d.books||[];
 if(!storeBooks.length){res.className='res empty';res.textContent='未找到相关书籍。';return}
 res.className='grid';
 res.innerHTML=storeBooks.map((x,i)=>`<div class=book data-i='${i}'><div class=cover>${cover(x)}</div><div class=meta><div class=t>${esc(x.title||'未命名')}</div><div class=a>${esc(x.author||'—')}</div></div></div>`).join('');
 res.querySelectorAll('.book').forEach(el=>el.onclick=()=>{const x=storeBooks[+el.dataset.i];openBook(x.book_id,{title:x.title,author:x.author,cover:x.cover})});
}
e('smode').querySelectorAll('button').forEach(b=>b.onclick=()=>{searchMode=b.dataset.m;e('smode').querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));e('q').placeholder=searchMode==='store'?'搜索微信读书书城（书名 / 作者）':'输入关键词，搜索划线和想法';e('results').className='res empty';e('results').textContent='输入关键词后搜索。'});
e('search').onsubmit=ev=>{ev.preventDefault();curQ=e('q').value.trim();if(!curQ)return;searchMode==='store'?doStoreSearch():doSearch(1)};
const modal=e('modal');
function closeBook(){modal.classList.remove('show');document.body.style.overflow=''}
modal.onclick=ev=>{if(ev.target===modal)closeBook()};
modal.addEventListener('click',ev=>{const btn=ev.target.closest('.cp');if(!btn)return;ev.stopPropagation();const item=btn.closest('.hl,.th,.pop,.rv'),tx=item&&item.querySelector('.tx');if(!tx)return;navigator.clipboard.writeText(tx.textContent.trim()).then(()=>{const old=btn.textContent;btn.textContent='✓';setTimeout(()=>{btn.textContent=old},1200)})});
document.addEventListener('keydown',ev=>{if(ev.key==='Escape')closeBook()});
function star(n){n=n||0;return n>0?'★'.repeat(Math.min(n,5)):''}
function renderMine(d){
 let body='<div class=bhtools><button id=copymd class=ghost>复制 Markdown</button></div><div class=notes>';
 const reviews=d.thoughts.filter(t=>t.is_book_review),ideas=d.thoughts.filter(t=>!t.is_book_review);
 if(reviews.length){body+=`<div class=ch>书评</div>`+reviews.map(t=>`<div class=th><div class=lb>书评 ${star(t.star)}</div><div class=tx>${esc(t.content||'')}</div><div class=ft><span class=date>${fmtDate(t.create_time)}</span><button class=cp type=button title=复制>${ICO.copy}</button></div></div>`).join('')}
 const ideaByCh={};ideas.forEach(t=>{(ideaByCh[t.chapter_uid]=ideaByCh[t.chapter_uid]||[]).push(t)});
 let curCh=null;const groups=[];
 d.highlights.forEach(h=>{const c=h.chapter_uid;if(c!==curCh){curCh=c;groups.push({uid:c,title:h.chapter_title,items:[]})}groups[groups.length-1].items.push(h)});
 if(!groups.length&&!ideas.length&&!reviews.length){body+='<div class=note-empty>这本书还没有划线或想法。</div>'}
 groups.forEach(g=>{body+=`<div class=ch>${esc(g.title||'未分章')}</div>`;
   g.items.forEach(h=>{body+=`<div class=hl data-c='${h.color_style||0}'><div class=tx>${esc(h.mark_text||'')}</div><div class=ft><span class=date>${fmtDate(h.create_time)}</span><button class=cp type=button title=复制>${ICO.copy}</button></div></div>`});
   (ideaByCh[g.uid]||[]).forEach(t=>{body+=`<div class=th><div class=lb>想法 ${star(t.star)}</div><div class=tx>${esc(t.content||'')}</div><div class=ft><span class=date>${fmtDate(t.create_time)}</span><button class=cp type=button title=复制>${ICO.copy}</button></div></div>`})});
 Object.keys(ideaByCh).forEach(uid=>{if(!groups.some(g=>String(g.uid)===String(uid))){body+=`<div class=ch>${esc(ideaByCh[uid][0].chapter_name||'想法')}</div>`+ideaByCh[uid].map(t=>`<div class=th><div class=lb>想法 ${star(t.star)}</div><div class=tx>${esc(t.content||'')}</div><div class=ft><span class=date>${fmtDate(t.create_time)}</span><button class=cp type=button title=复制>${ICO.copy}</button></div></div>`).join('')}});
 return body+'</div>';
}
async function openBook(id,store){if(!id)return;modal.classList.add('show');document.body.style.overflow='hidden';e('sheet').innerHTML='<div class=note-empty>加载中…</div>';
 let mine=null;
 if(!store){const d=await fetch('/api/book?book_id='+encodeURIComponent(id)).then(r=>r.json());if(!d.error)mine=d}
 const b=mine?mine.book:(store||{}),p=Math.max(0,Math.min(100,b.reading_progress||0));
 const tabs=mine?['mine','popular','reviews']:['popular','reviews'];const LABEL={mine:'我的笔记',popular:'热门划线',reviews:'书评'};
 const meta=mine?`${b.rating?`<span class=chip>推荐 ${(b.rating/10).toFixed(1)}%</span>`:''}${b.word_count?`<span class=chip>${(b.word_count/10000).toFixed(1)} 万字</span>`:''}${b.publisher?`<span class=chip>${esc(b.publisher)}</span>`:''}`:'';
 const st=mine?`<div class=st><span class=chip>进度 ${p}%</span><span class=chip>划线 ${mine.highlights.length}</span><span class=chip>想法 ${mine.thoughts.length}</span>${b.category?`<span class=chip>${esc(b.category)}</span>`:''}${meta}</div>`:'';
 const intro=mine&&b.intro?`<div class=bkintro>${esc(b.intro)}</div>`:'';
 const header=`<div class=bh><div class=cover>${cover(b)}</div><div class=bi><h3>${esc(b.title||'未命名')}</h3><div class=a>${esc(b.author||'—')}</div>${st}${intro}</div><div class=bhx>${b.weread_url?`<a class=wr href='${esc(b.weread_url)}' target=_blank rel=noopener title='在微信读书中打开'>${ICO.ext}微信读书</a>`:''}<button class=x type=button title=关闭>×</button></div></div>`;
 const tabbar=`<div class=tabs>${tabs.map((t,i)=>`<button data-t='${t}' type=button class='${i===0?'on':''}'>${LABEL[t]}</button>`).join('')}</div>`;
 e('sheet').innerHTML=header+tabbar+`<div id=tabwrap></div>`;
 e('sheet').querySelector('.x').onclick=closeBook;
 const bi=e('sheet').querySelector('.bkintro');if(bi)bi.onclick=()=>bi.classList.toggle('open');
 const cache={};
 async function show(t){
  e('sheet').querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x.dataset.t===t));
  const wrap=e('tabwrap');
  if(t==='mine'){wrap.innerHTML=renderMine(mine);const c=e('copymd');if(c)c.onclick=()=>navigator.clipboard.writeText(toMarkdown(mine)).then(()=>{c.textContent='已复制 ✓';setTimeout(()=>c.textContent='复制 Markdown',1500)});return}
  if(cache[t]){wrap.innerHTML=cache[t];return}
  wrap.innerHTML='<div class=note-empty>加载中…</div>';
  const data=await fetch(`/api/book-extra?book_id=${encodeURIComponent(id)}&kind=${t}`).then(r=>r.json());
  if(data.error){wrap.innerHTML=`<div class=note-empty>${esc(data.error)}</div>`;return}
  let html;
  if(t==='popular'){const its=data.items||[];html='<div class=notes>'+(its.length?its.map(x=>`<div class=pop><div class=tx>${esc(x.markText||'')}</div><div class=ft><span>${esc(x.chapter||'')}</span><span>${x.count} 人划线 · <button class=cp type=button title=复制>${ICO.copy}</button></span></div></div>`).join(''):'<div class=note-empty>暂无热门划线。</div>')+'</div>'}
  else{const rs=data.reviews||[];html='<div class=notes>'+(rs.length?rs.map(x=>`<div class=rv><div class=au><span>${esc(x.author||'匿名')} ${star(x.star)}</span><span>${x.likes} 赞</span></div><div class=tx>${esc(x.content||'')}</div><div class=ft><button class=cp type=button title=复制>${ICO.copy}</button></div></div>`).join(''):'<div class=note-empty>暂无公开书评。</div>')+'</div>'}
  cache[t]=html;wrap.innerHTML=html;
 }
 e('sheet').querySelectorAll('.tabs button').forEach(btn=>btn.onclick=()=>show(btn.dataset.t));
 show(tabs[0]);
}
function toMarkdown(d){const b=d.book;let m=`# ${b.title||'未命名'}\n\n> ${b.author||''}${b.category?' · '+b.category:''}\n\n`;
 const reviews=d.thoughts.filter(t=>t.is_book_review),ideas=d.thoughts.filter(t=>!t.is_book_review);
 reviews.forEach(t=>{m+=`## 书评\n\n${t.content||''}  \n*${fmtDate(t.create_time)}*\n\n`});
 const ideaByCh={};ideas.forEach(t=>{(ideaByCh[t.chapter_uid]=ideaByCh[t.chapter_uid]||[]).push(t)});
 let curCh=null;const groups=[];d.highlights.forEach(h=>{const c=h.chapter_uid;if(c!==curCh){curCh=c;groups.push({uid:c,title:h.chapter_title,items:[]})}groups[groups.length-1].items.push(h)});
 groups.forEach(g=>{m+=`## ${g.title||'未分章'}\n\n`;g.items.forEach(h=>{m+=`> ${(h.mark_text||'').replace(/\n/g,' ')}  \n*${fmtDate(h.create_time)}*\n\n`});(ideaByCh[g.uid]||[]).forEach(t=>{m+=`💭 ${t.content||''}  \n*${fmtDate(t.create_time)}*\n\n`})});
 return m}
const fmtHours=s=>Math.round((s||0)/360)/10;
function barChart(data,opts){opts=opts||{};const W=opts.w||520,H=opts.h||140,pad=22,n=Math.max(1,data.length);
 const max=Math.max(1,...data.map(d=>d.value));const step=(W-pad*2)/n,bw=Math.min(step*0.6,30);
 const bars=data.map((d,i)=>{const bh=(H-26)*(d.value/max);const x=pad+i*step+(step-bw)/2,y=H-18-bh;
  return `<rect x='${x.toFixed(1)}' y='${y.toFixed(1)}' width='${bw.toFixed(1)}' height='${Math.max(bh,1).toFixed(1)}' rx='3' fill='var(--brand)'><title>${esc(String(d.label||''))} ${fmtHours(d.value)}h</title></rect>`+(d.tick!==''?`<text x='${(x+bw/2).toFixed(1)}' y='${H-5}' text-anchor='middle' class='caxis'>${esc(String(d.tick))}</text>`:'')}).join('');
 return `<svg viewBox='0 0 ${W} ${H}' class='chart' preserveAspectRatio='xMidYMid meet'>${bars}</svg>`}
document.querySelectorAll('.nav button').forEach(b=>{const k={shelf:'book',stats:'stats',search:'search',sync:'sync'}[b.dataset.view];if(k)b.insertAdjacentHTML('afterbegin',ICO[k]);b.onclick=()=>{const v=b.dataset.view;document.querySelectorAll('.nav button').forEach(x=>x.classList.toggle('on',x===b));document.querySelectorAll('.view').forEach(s=>{s.hidden=s.dataset.view!==v})}});
async function loadStats(){let d=await fetch('/api/stats').then(r=>r.json());const sec=e('stats');
 if(!d.hasData){sec.className='empty';sec.innerHTML='暂无统计数据，先到「同步设置」同步一次。';return}
 const o=d.overall;e('stats-word').textContent=o.preferCategoryWord||'';
 const stat=(o.readStat||[]).map(s=>`<span class=chip>${esc(s.stat)} ${esc(s.counts)}</span>`).join('');
 const head=`<div class=panel><div class=big><div><span class=v>${fmtHours(o.totalReadTime)}</span> <span class=l>小时总阅读</span></div><div><span class=v>${o.readDays}</span> <span class=l>天</span></div><div><span class=v>${o.authorCount}</span> <span class=l>位作者</span></div></div><div class=chips style=margin-top:10px>${stat}</div></div>`;
 const yc=`<div class=panel><h3>按年阅读时长</h3>${barChart(o.byYear.map(y=>({label:y.label,tick:y.label,value:y.seconds})))}</div>`;
 const hc=`<div class=panel><h3>时段分布 · ${esc(o.preferTimeWord||'')}</h3>${barChart((o.preferTime||[]).map((v,i)=>({label:i+'时',tick:i%6===0?i:'',value:v})),{h:120})}</div>`;
 const cmax=Math.max(1,...o.categories.map(c=>c.seconds));
 const cats=`<div class=panel><h3>偏好分类 Top</h3>${o.categories.map(c=>`<div class=hbar><span class=nm>${esc(c.title||'')}</span><span class=tk><i style="width:${(c.seconds/cmax*100).toFixed(0)}%"></i></span><span class=vv>${fmtHours(c.seconds)}h</span></div>`).join('')}</div>`;
 const auth=`<div class=panel><h3>常读作者 Top</h3>${o.authors.map(a=>`<div class=hbar><span class=nm style='flex:1;width:auto'>${esc(a.name||'')}</span><span class=vv style='width:auto;white-space:nowrap'>${esc(a.readTime||'')} · ${a.count}本</span></div>`).join('')}</div>`;
 const sd=d.sessions||{distribution:[],total:0},smax=Math.max(1,...sd.distribution.map(x=>x.count));
 const sess=`<div class=panel><h3>单次阅读时长分布 · 据划线时间推断，共 ${sd.total} 次</h3>${sd.distribution.map(x=>`<div class=hbar><span class=nm>${esc(x.label)}</span><span class=tk><i style="width:${(x.count/smax*100).toFixed(0)}%"></i></span><span class=vv>${x.count} 次</span></div>`).join('')}<div style='font-size:11px;color:var(--muted);margin-top:10px'>同一时段连续划线视为一次阅读，跨度即时长；纯阅读未划线的部分无法计入，仅供参考“碎片 vs 整片”的倾向。</div></div>`;
 sec.className='';sec.innerHTML=head+`<div class=stats-grid>${yc}${hc}</div><div style='margin-top:14px'>${sess}</div><div class=stats-grid>${cats}${auth}</div>`}
loadSettings();load();loadStats();</script></body></html>""".encode("utf-8")


def make_handler(db_path: Path):
    sync_lock = threading.Lock()

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
                elif parsed.path == "/api/settings":
                    source = api_key_source()
                    _json(
                        self,
                        {
                            "api_key_configured": source != "none",
                            "source": source,
                            "config_path": str(default_config_path()),
                        },
                    )
                elif parsed.path == "/api/summary":
                    _json(self, summary(conn))
                elif parsed.path == "/api/stats":
                    _json(self, _reading_stats(conn))
                elif parsed.path == "/api/books":
                    limit = min(max(int(query.get("limit", [20])[0]), 1), 5000)
                    rows = conn.execute(
                        """SELECT book_id,title,author,cover,category,total_notes,reading_progress,finished,sort,
                        rating,word_count FROM books ORDER BY sort DESC LIMIT ?""",
                        (limit,),
                    ).fetchall()
                    _json(self, [dict(row) for row in rows])
                elif parsed.path == "/api/book":
                    book_id = query.get("book_id", [""])[0].strip()
                    if not book_id:
                        _json(self, {"error": "缺少 book_id"}, HTTPStatus.BAD_REQUEST)
                        return
                    book = conn.execute(
                        """SELECT book_id,title,author,cover,intro,category,publish_time,
                        total_notes,reading_progress,review_count,note_count,bookmark_count,finished,
                        rating,rating_count,word_count,publisher,isbn,translator
                        FROM books WHERE book_id=?""",
                        (book_id,),
                    ).fetchone()
                    if book is None:
                        _json(self, {"error": "not found"}, HTTPStatus.NOT_FOUND)
                        return
                    highlights = conn.execute(
                        """SELECT chapter_uid,chapter_title,mark_text,color_style,create_time
                        FROM highlights WHERE book_id=? ORDER BY chapter_uid, create_time""",
                        (book_id,),
                    ).fetchall()
                    thoughts = conn.execute(
                        """SELECT chapter_uid,chapter_name,content,star,is_book_review,text_range,create_time
                        FROM thoughts WHERE book_id=? ORDER BY is_book_review DESC, create_time""",
                        (book_id,),
                    ).fetchall()
                    book_dict = dict(book)
                    book_dict["weread_url"] = weread_url(book_id)
                    _json(
                        self,
                        {
                            "book": book_dict,
                            "highlights": [dict(row) for row in highlights],
                            "thoughts": [dict(row) for row in thoughts],
                        },
                    )
                elif parsed.path == "/api/book-extra":
                    # Live proxy to the WeRead Skill: other readers' popular highlights / public reviews.
                    book_id = query.get("book_id", [""])[0].strip()
                    kind = query.get("kind", ["popular"])[0]
                    if not book_id:
                        _json(self, {"error": "缺少 book_id"}, HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        if kind == "reviews":
                            data = Gateway().call("/review/list", bookId=book_id, count=20)
                            reviews = []
                            for wrapper in data.get("reviews", []):
                                review = (wrapper.get("review") or {}).get("review") or {}
                                content = review.get("content")
                                if not content:
                                    continue
                                reviews.append({
                                    "content": content,
                                    "star": int((review.get("star") or 0) / 20),
                                    "author": (review.get("author") or {}).get("name"),
                                    "likes": int((wrapper.get("review") or {}).get("likesCount") or 0),
                                })
                            _json(self, {"reviews": reviews})
                        else:
                            data = Gateway().call("/book/bestbookmarks", bookId=book_id)
                            chapters = {c.get("chapterUid"): c.get("title") for c in (data.get("chapters") or [])}
                            items = [
                                {"markText": it.get("markText"), "count": it.get("totalCount") or 0,
                                 "chapter": chapters.get(it.get("chapterUid"))}
                                for it in (data.get("items") or []) if it.get("markText")
                            ]
                            _json(self, {"items": items})
                    except Exception as error:  # noqa: BLE001 — surfaced to the page
                        _json(self, {"error": str(error)})
                elif parsed.path == "/api/store-search":
                    keyword = query.get("q", [""])[0].strip()
                    if not keyword:
                        _json(self, {"books": []})
                        return
                    try:
                        data = Gateway().call("/store/search", keyword=keyword, count=20)
                        books = []
                        for tab in data.get("results", []):
                            for entry in (tab.get("books") or []):
                                info = entry.get("bookInfo") or {}
                                if info.get("bookId"):
                                    # Store covers come as low-res `s_`; request a sharper size.
                                    cover = (info.get("cover") or "").replace("/s_", "/t7_")
                                    books.append({"book_id": info["bookId"], "title": info.get("title"),
                                                  "author": info.get("author"), "cover": cover,
                                                  "weread_url": weread_url(info["bookId"])})
                        seen, unique = set(), []
                        for book in books:
                            if book["book_id"] not in seen:
                                seen.add(book["book_id"])
                                unique.append(book)
                        _json(self, {"books": unique[:24]})
                    except Exception as error:  # noqa: BLE001 — surfaced to the page
                        _json(self, {"error": str(error)})
                elif parsed.path == "/api/search":
                    term = query.get("q", [""])[0].strip()
                    if not term:
                        _json(self, {"total": 0, "page": 1, "page_size": 20, "rows": []})
                        return
                    page = max(int(query.get("page", [1])[0]), 1)
                    page_size = 20
                    needle = f"%{term}%"
                    union = """SELECT b.book_id AS book_id,b.title AS title,'划线' AS kind,h.chapter_title AS chapter,
                            h.mark_text AS content,h.create_time AS created
                            FROM highlights h JOIN books b ON b.book_id=h.book_id WHERE h.mark_text LIKE ?
                          UNION ALL
                          SELECT b.book_id,b.title,'想法',t.chapter_name,t.content,t.create_time
                            FROM thoughts t JOIN books b ON b.book_id=t.book_id WHERE t.content LIKE ?"""
                    total = conn.execute(
                        f"SELECT count(*) AS n FROM ({union})", (needle, needle)
                    ).fetchone()["n"]
                    rows = conn.execute(
                        f"SELECT * FROM ({union}) ORDER BY created DESC LIMIT ? OFFSET ?",
                        (needle, needle, page_size, (page - 1) * page_size),
                    ).fetchall()
                    _json(
                        self,
                        {
                            "total": total,
                            "page": page,
                            "page_size": page_size,
                            "rows": [dict(row) for row in rows],
                        },
                    )
                else:
                    _json(self, {"error": "not found"}, 404)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/sync/stream":
                self._sync_stream()
                return
            if parsed.path == "/api/settings/api-key":
                try:
                    body = _read_json_body(self)
                    api_key = str(body.get("api_key", "")).strip()
                    if not api_key:
                        _json(self, {"error": "API Key 不能为空。"}, HTTPStatus.BAD_REQUEST)
                        return
                    path = save_api_key(api_key)
                    _json(self, {"status": "ok", "source": "config", "config_path": str(path)})
                except (OSError, ValueError, json.JSONDecodeError) as error:
                    _json(self, {"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            if parsed.path != "/api/sync":
                _json(self, {"error": "not found"}, 404)
                return
            if not sync_lock.acquire(blocking=False):
                _json(self, {"error": "已有同步正在运行，请稍后再试。"}, HTTPStatus.CONFLICT)
                return
            try:
                try:
                    mode = str(_read_json_body(self).get("mode", "notes"))
                except json.JSONDecodeError:
                    mode = "notes"
                with connect(db_path) as conn:
                    counts = _sync_counts(SyncService(conn, Gateway(), report=lambda _: None), mode)
                _json(self, {"status": "ok", "mode": mode, "counts": counts})
            except ValueError as error:
                _json(self, {"error": str(error)}, HTTPStatus.BAD_REQUEST)
            except Exception as error:
                _json(self, {"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            finally:
                sync_lock.release()

        def _sync_stream(self) -> None:
            # One button: refresh the shelf (fast, indeterminate progress) then sync notes
            # incrementally (determinate i/N progress) and append stat snapshots — streamed as
            # newline-delimited JSON so the page shows a live, moving progress bar throughout.
            try:
                mode = str(_read_json_body(self).get("mode", "sync"))
            except json.JSONDecodeError:
                mode = "sync"
            if not sync_lock.acquire(blocking=False):
                _json(self, {"error": "已有同步正在运行，请稍后再试。"}, HTTPStatus.CONFLICT)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "close")
            self.end_headers()

            def emit(obj: dict[str, object]) -> None:
                try:
                    self.wfile.write((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, ValueError):
                    pass

            try:
                emit({"line": "正在同步书架…（首次可能较慢）"})
                with connect(db_path) as conn:
                    service = SyncService(conn, Gateway(), report=lambda message: emit({"line": message}))
                    counts = {"shelf": 0, "books": 0, "notes": 0, "stats": 0}
                    counts["shelf"] = service.shelf()
                    counts["books"] = service.books()
                    emit({"line": "书架已就绪，开始同步笔记…"})
                    counts["notes"] = service.notes(full=(mode == "full"))
                    emit({"line": "同步阅读统计…"})
                    counts["stats"] = service.stats()
                    emit({"done": True, "counts": counts})
            except Exception as error:  # noqa: BLE0001 — surfaced to the page as a stream error line
                emit({"error": str(error)})
            finally:
                sync_lock.release()
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
