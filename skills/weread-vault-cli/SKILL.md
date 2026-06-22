---
name: weread-vault-cli
description: Use when a user wants to sync, inspect, search, export, back up, or preview their local WeRead Vault database with the weread-vault CLI. This skill covers safe local-first operations and requires WEREAD_API_KEY only for a sync.
---

# WeRead Vault CLI

`weread-vault` stores WeRead metadata, highlights, reviews, and reading-stat snapshots in a local SQLite database. Its web preview reads this local database only.

## Safety rules

- Never print, save, commit, or paste `WEREAD_API_KEY`.
- The default database is per-user. Check `weread-vault status` before passing `--db` so a user's data is not unintentionally mixed.
- Run `sync` only when the user asked to refresh remote data. Searching, exporting, serving, and backing up do not need the API key.
- If the gateway says the upstream Skill must be upgraded, stop the sync. Update the repository submodule before retrying; do not guess a newer protocol version.

## Install and initialize

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

## Inspect and preview

```bash
weread-vault status
weread-vault serve --open
```

`serve` binds only to `127.0.0.1` and defaults to port `8765`. For a different local port:

```bash
weread-vault serve --port 8899 --open
```

## Export and backup

```bash
weread-vault export markdown --out ~/Documents/weread-notes
weread-vault backup --out ~/Backups/weread-vault.db
```

The backup command uses SQLite's backup API, so it remains consistent even if the web preview is open.

## Update the official protocol Skill

The repository vendors Tencent's official `WeChatReading` repository as a git submodule. From the repository root:

```bash
./scripts/update-official-skill.sh
```

Review the resulting submodule commit before committing it. The CLI's gateway version must be updated deliberately and tested when the official Skill changes.
