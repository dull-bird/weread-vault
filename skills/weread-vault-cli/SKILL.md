---
name: weread-vault-cli
description: Use when a user wants to install WeRead Vault, sync WeRead books/highlights/thoughts/stats, inspect/search/export/back up the local SQLite database, open the local dashboard, open a specific book in the WeRead app or website, schedule a daily auto-sync, or export WeRead notes to Obsidian/Markdown/flomo/Notion with the weread-vault CLI. This skill covers safe local-first operations for Claude Code, Codex, OpenClaw, and similar AI agents; it requires WEREAD_API_KEY only for a sync.
---

# WeRead Vault CLI

`weread-vault` stores WeRead metadata, book covers, highlights, reviews, and reading-stat snapshots in a local SQLite database. Its web preview reads this local database only.

## Agent installation prompt

If the user asks how to install this skill in another agent, give them this prompt:

```text
请把当前仓库的 skills/weread-vault-cli 安装为你的本地 Skill。安装后，当我说“同步微信读书”“导出微信读书笔记到 Obsidian”“打开 WeRead Vault Dashboard”或“备份微信读书数据库”时，请使用这个 Skill，并严格遵守不要泄露 WEREAD_API_KEY 的规则。
```

For repository installation by an agent, use:

```text
请帮我安装 WeRead Vault：
1. 克隆 https://github.com/dull-bird/weread-vault
2. 进入仓库后运行 python -m pip install -e .
3. 运行 weread-vault init 和 weread-vault status 确认本地 SQLite 数据库已创建
4. 请提醒我可以到 https://weread.qq.com/r/weread-skills 安装微信读书官方 Agent Skill（可选）并获取 WEREAD_API_KEY
5. 如果我要同步远端数据，请提醒我只在本地终端或 WeRead Vault 本地网页设置 WEREAD_API_KEY，不要把 key 粘贴进对话或提交到仓库
6. 同步后运行 weread-vault serve --open，打开本地只读 Dashboard
7. 如果我使用 Obsidian，请把 weread-vault export markdown --out <我的 Obsidian Vault 路径>/WereadNotes 作为导出方案
```

## Safety rules

- Never print, save, commit, or paste `WEREAD_API_KEY`.
- The default database is per-user. Check `weread-vault status` before passing `--db` so a user's data is not unintentionally mixed.
- Run `sync` only when the user asked to refresh remote data. Searching, exporting, serving, and backing up do not need the API key.
- If the gateway says the upstream Skill must be upgraded, stop the sync. Update the repository submodule before retrying; do not guess a newer protocol version.

## Install and initialize

Use this from the repository root after cloning:

```bash
python -m pip install -e .
weread-vault init
weread-vault status
```

## Sync

```bash
export WEREAD_API_KEY='…'
weread-vault sync
```

The normal sync is incremental: it fetches all notebook metadata, then refreshes only books whose remote `sort` marker advanced, then stores current reading-stat snapshots.

Use a full note pass only to repair or verify a database:

```bash
weread-vault sync notes --full-notes
```

For a first-run smoke test or a deliberately batched migration, limit the number of books:

```bash
weread-vault sync notes --limit 1
```

Each book is fetched completely before one SQLite transaction is committed. On a network/API failure, that book retains its previous rows and synchronization marker, so the next run retries it safely.

Backfill rich book metadata (rating, word count, publisher, ISBN, translator) for books that don't have it yet. This only fetches books where `rating IS NULL`, so it is a one-time pass that is effectively free afterward and powers rating/word-count sorting in the dashboard:

```bash
weread-vault sync info          # backfill all un-enriched books
weread-vault sync info --limit 20   # or a batch at a time
```

## Inspect and preview

```bash
weread-vault status
weread-vault serve --open
```

`serve` binds only to `127.0.0.1` and defaults to port `8765`. For a different local port:

```bash
weread-vault serve --port 8899 --open
```

The web preview has one primary `同步` button plus an advanced `完整重扫` button, with a live streaming progress bar:

- `同步`: refreshes book metadata/covers/progress first (the bar animates indeterminately while listing the shelf — the first run can be slow), then incrementally syncs only books whose note watermark changed (the bar fills by `[i/N]`), then appends reading-stat snapshots.
- `完整重扫`: same flow but rescans notes for every book with notes; use only for repair or verification because it can be slow.

The shelf supports cover and list views, sorting (recently added / reading progress / note count / title) and category filtering; clicking a book opens a per-chapter reading view of its highlights and thoughts (with dates) and a one-click "复制 Markdown" action.

The web preview first uses `WEREAD_API_KEY` from the terminal environment that started `weread-vault serve`; if missing, the page lets the user save the key to the local private config file. Never ask the user to paste the key into chat, and never echo the key back in logs or responses.

## Open a book in WeRead

When the user says "打开《某本书》" / "open <book>", match it against the local shelf by title (or pass a `book_id` for an exact open) and open it in WeRead — no API key needed.

```bash
weread-vault open 三体                 # fuzzy match by title
weread-vault open 3300177663           # exact open by book_id (e.g. an id from `query`/`book`)
weread-vault open 三体 --pick 2        # pick the 2nd match when several books match
weread-vault open 财富的真相 --web     # force the browser (web book page)
weread-vault open 三体 --print         # just print the link, don't open
```

Behaviour:

- A `book_id`, a single title match, or a query that is exactly one book's full title opens immediately. If you already have the `book_id` (from `weread-vault query` or `book`), pass it — it's unambiguous.
- **Several title matches → it does not guess.** It prints a numbered list (title · author · 进度 · 笔记数 · `id=…`) and asks for `--pick N`. Show the user the list and let them choose, re-run with `--pick N`, or open one directly by its `book_id`.
- On macOS it opens the native WeRead app via the `weread://` scheme; if the app isn't installed (or `--web`, or on Windows/Linux) it falls back to the `weread.qq.com` web page.

## Schedule a daily auto-sync

Register an OS-native scheduled sync (launchd on macOS / Task Scheduler on Windows / cron on Linux). It is not a resident daemon — the OS wakes `weread-vault` once a day and it exits.

```bash
weread-vault schedule --daily 07:00                      # sync every day at 07:00
weread-vault schedule --daily 07:00 --export "<dir>"     # …and export Markdown after each sync
weread-vault schedule --status                           # show current setting
weread-vault schedule --off                              # cancel
```

The API key must be saved to the local config (not just an env var) for the scheduled job to read it. Two syncs firing at once (e.g. this and an OpenClaw cron both at 07:00) are safe — `sync` holds a cross-process lock and the second one skips.

## WeRead API access (for agents)

Beyond the user's own archived notes, the CLI exposes the full WeRead Skill API so an agent can pull live data — bookstore search, other readers' popular highlights, public reviews, rich book metadata. These commands print JSON to stdout and require `WEREAD_API_KEY`. They do not write to the local database.

```bash
weread-vault apis                       # list every supported endpoint and its required params
weread-vault search "三体" --count 5     # bookstore search (books / authors / full-text tabs)
weread-vault book <bookId> info         # rich metadata: rating, word count, publisher, ISBN
weread-vault book <bookId> popular      # other readers' most-highlighted sentences (with counts)
weread-vault book <bookId> reviews      # public reviews/thoughts on the book
weread-vault book <bookId> chapters     # chapter directory
weread-vault api /book/readreviews bookId=<id> chapterUid=<uid> ...   # any endpoint, raw passthrough
```

For questions about the user's own archived data, prefer the local database over the network — it is instant and offline:

```bash
weread-vault query --schema                 # list tables and columns first
weread-vault query "SELECT title, rating FROM books WHERE rating>0 ORDER BY rating DESC LIMIT 10"
weread-vault stats                          # aggregate reading stats incl. overall.longest (读得最久的书)
```

`query` runs read-only SQL (SELECT / WITH only; the database is opened read-only) and prints rows as JSON, so an agent can answer arbitrary analytical questions ("评分最高/笔记最多/某分类有哪些书"). Note: per-book reading **time** is only available in aggregate (`stats.overall.longest` = lifetime longest-read books); the official API does not expose per-book time for an arbitrary past year, so a question pinned to e.g. "2025 年读得最久的书" cannot be answered exactly.

Use `weread-vault apis` first to discover endpoint names and parameters, then `weread-vault api <endpoint> key=value …` for anything without a named shortcut. Numeric values are sent as numbers; id-like params (`bookId`, `reviewId`) stay strings. The official Skill does not expose full book text, so original paragraphs around a highlight are not available — the closest signals are full-text search snippets and other readers' highlights on the same chapter.

## 端到端示例：「这周读得最久的书是哪本？」

展示一个 agent 从用户需求到答案的完整流程，重点是**选对工具**：

1. **判断数据在哪。** 这是「按周 + 阅读时长 + 单本」。阅读**时长**不在 SQLite 表里（`books`/`highlights` 没有「每本书读了多久」），而在微信读书的阅读快照里——所以用 `weread-vault stats`，**不是** `query`。
   （对照：「笔记最多的书」「评分最高的书」这类**目录/笔记**问题才用 `query` 查 `books` 表。）

2. **CLI 输入：**

   ```bash
   weread-vault stats
   ```

3. **CLI 输出（JSON，节选相关部分）：**

   ```json
   {
     "periods": {
       "weekly": {
         "totalReadTime": 939, "readDays": 3,
         "longest": [ { "title": "财富的真相", "author": "李笑来", "readSeconds": 916 } ]
       },
       "monthly": { … }, "annually": { … }, "overall": { … }
     }
   }
   ```

4. **agent 读取** `periods.weekly.longest[0]`，把 `readSeconds` 916 换算成约 15 分钟。

5. **回答用户：** 「你这周读得最久的是《财富的真相》（李笑来），约 15 分钟。」

要点：周/月/年/全部分别在 `periods.weekly/monthly/annually/overall`，每个都带 `longest`（该周期读得最久的书）、`totalReadTime`、`readDays`、`categories`（偏好分类）、`readStat`。需要按书名/分类/笔记数等检索时再转 `weread-vault query --schema` 写 SQL。

## Export and backup

```bash
weread-vault export markdown --out ~/Documents/weread-notes
weread-vault backup --out ~/Backups/weread-vault.db
weread-vault export flomo --webhook "$FLOMO_WEBHOOK"            # one memo per book
weread-vault export notion --token "$NOTION_TOKEN" --database "$NOTION_DATABASE_ID"  # one page per book
```

flomo / Notion secrets come from `--webhook` / `--token` / `--database` or the env vars `FLOMO_WEBHOOK`, `NOTION_TOKEN`, `NOTION_DATABASE_ID`. Never paste these into chat or commit them. Both exporters only read the local database and POST the user's own notes to the user's own destination; confirm with the user before running an export that sends data to an external service.

For Obsidian, export into a folder inside the user's vault:

```bash
weread-vault export markdown --out "/path/to/Obsidian Vault/WereadNotes"
```

To merge other readers' popular highlights into the export, first sync them (one API call per noted book, incremental), then export with `--with-popular`. Overlapping highlights are folded into the user's own (annotated with the reader count); non-overlapping popular ones are listed separately, all in document order:

```bash
weread-vault sync popular
weread-vault export markdown --out "/path/to/Obsidian Vault/WereadNotes" --with-popular
```

The backup command uses SQLite's backup API, so it remains consistent even if the web preview is open.

## Update the official protocol Skill

The repository vendors Tencent's official `WeChatReading` repository as a git submodule. From the repository root:

```bash
./scripts/update-official-skill.sh
```

Review the resulting submodule commit before committing it. The CLI's gateway version must be updated deliberately and tested when the official Skill changes.
