---
name: weread-vault-cli
description: Use when a user wants to install WeRead Vault, sync WeRead books/highlights/thoughts/stats, inspect/search/export/back up the local SQLite database, open the local dashboard, or export WeRead notes to Obsidian/Markdown with the weread-vault CLI. This skill covers safe local-first operations for Claude Code, Codex, OpenClaw, and similar AI agents; it requires WEREAD_API_KEY only for a sync.
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

Use `weread-vault apis` first to discover endpoint names and parameters, then `weread-vault api <endpoint> key=value …` for anything without a named shortcut. Numeric values are sent as numbers; id-like params (`bookId`, `reviewId`) stay strings. The official Skill does not expose full book text, so original paragraphs around a highlight are not available — the closest signals are full-text search snippets and other readers' highlights on the same chapter.

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

The backup command uses SQLite's backup API, so it remains consistent even if the web preview is open.

## Update the official protocol Skill

The repository vendors Tencent's official `WeChatReading` repository as a git submodule. From the repository root:

```bash
./scripts/update-official-skill.sh
```

Review the resulting submodule commit before committing it. The CLI's gateway version must be updated deliberately and tested when the official Skill changes.
