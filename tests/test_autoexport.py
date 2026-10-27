from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from weread_vault import autoexport, integrations
from weread_vault.config import save_config
from weread_vault.db import connect, get_state, initialize


def _seed_book(conn, book_id: str, sort: int) -> None:
    conn.execute(
        "INSERT INTO books(book_id,title,author,category,total_notes,reading_progress,sort,synced_at)"
        " VALUES(?,?, '作者','经济理财-理财',1,50,?,0)",
        (book_id, f"书{book_id}", sort),
    )
    conn.execute(
        "INSERT INTO highlights(bookmark_id,book_id,chapter_uid,chapter_title,mark_text,text_range,create_time,updated_at)"
        " VALUES(?,?,1,'第一章','一句划线',?,1,1)",
        (f"m-{book_id}", book_id, f"0-{sort}"),
    )


class AutoExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "vault.db"
        self.cfg = self.root / "config.json"
        self.out = self.root / "obsidian"
        initialize(self.db_path)
        with connect(self.db_path) as conn:
            _seed_book(conn, "b1", 100)
            _seed_book(conn, "b2", 200)
            conn.commit()
        # Route flomo/Notion through a stub poster so no network happens.
        self.flomo, self.notion = [], []
        self._orig = integrations._http_post

        def stub(url, payload, headers, method="POST"):
            (self.flomo if "flomo" in url else self.notion).append(url)
            return {"id": "page"}

        integrations._http_post = stub
        # export_* capture the default poster at def-time, so patch their defaults too.
        integrations.export_flomo.__defaults__ = (None, stub, None)
        integrations.export_notion.__defaults__ = (None, stub, None)
        self.addCleanup(self._restore)

    def _restore(self):
        integrations._http_post = self._orig
        integrations.export_flomo.__defaults__ = (None, self._orig, None)
        integrations.export_notion.__defaults__ = (None, self._orig, None)

    def _configure_all(self, *, auto=True):
        save_config("export_markdown_dir", str(self.out), self.cfg)
        save_config("flomo_webhook", "https://flomoapp.com/iwh/xxx", self.cfg)
        save_config("notion_token", "secret_x", self.cfg)
        save_config("notion_database", "db_x", self.cfg)
        if auto:
            for target in ("markdown", "flomo", "notion"):
                autoexport.set_auto(target, True, self.cfg)

    def _run(self):
        with connect(self.db_path) as conn:
            return autoexport.run_auto_exports(conn, report=lambda _m: None, config_path=self.cfg)

    def test_configured_targets_reflects_config(self):
        self.assertEqual(autoexport.configured_targets(self.cfg), [])
        self._configure_all()
        self.assertEqual(autoexport.configured_targets(self.cfg), ["markdown", "flomo", "notion"])

    def test_first_run_exports_all_then_incremental(self):
        self._configure_all()
        results = self._run()
        self.assertEqual({r["target"]: r.get("count") for r in results},
                         {"markdown": 2, "flomo": 2, "notion": 2})
        self.assertEqual(sorted(p.name for p in self.out.glob("*.md")), ["书b1.md", "书b2.md"])
        self.assertEqual(len(self.flomo), 2)
        self.assertEqual(len(self.notion), 2)

        # Nothing changed: markdown re-scans (0 rewrites), flomo/Notion send nothing.
        self.flomo.clear(); self.notion.clear()
        results = self._run()
        self.assertEqual({r["target"]: r.get("count") for r in results},
                         {"markdown": 0, "flomo": 0, "notion": 0})
        self.assertEqual(len(self.flomo), 0)
        self.assertEqual(len(self.notion), 0)

        # A book whose watermark advanced is the only thing re-exported.
        with connect(self.db_path) as conn:
            _seed_book(conn, "b3", 300)
            conn.commit()
        self.flomo.clear(); self.notion.clear()
        results = self._run()
        self.assertEqual({r["target"]: r.get("count") for r in results},
                         {"markdown": 1, "flomo": 1, "notion": 1})

    def test_watermark_persisted_in_sync_state(self):
        self._configure_all()
        self._run()
        with connect(self.db_path) as conn:
            self.assertEqual(get_state(conn, "export_flomo_sort"), "200")
            self.assertEqual(get_state(conn, "export_notion_sort"), "200")

    def test_one_failing_target_does_not_abort_others(self):
        self._configure_all()

        def boom(url, payload, headers, method="POST"):
            if "notion" in url:
                raise RuntimeError("boom")
            self.flomo.append(url)
            return {}

        integrations.export_flomo.__defaults__ = (None, boom, None)
        integrations.export_notion.__defaults__ = (None, boom, None)
        results = {r["target"]: r["status"] for r in self._run()}
        self.assertEqual(results["markdown"], "success")
        self.assertEqual(results["flomo"], "success")
        self.assertEqual(results["notion"], "failed")
        # The failure is recorded as a sync_runs row so `weread-vault log` shows it.
        with connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT status, detail FROM sync_runs WHERE scope='export:notion' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        self.assertEqual(row["status"], "failed")
        self.assertIn("boom", row["detail"])

    def test_no_targets_is_a_noop(self):
        self.assertEqual(self._run(), [])

    def test_saved_but_auto_off_is_not_exported(self):
        # Credentials saved (for manual export) but auto-export left off → sync must not fan out.
        self._configure_all(auto=False)
        self.assertEqual(autoexport.saved_targets(self.cfg), ["markdown", "flomo", "notion"])
        self.assertEqual(autoexport.configured_targets(self.cfg), [])
        self.assertEqual(self._run(), [])
        # Enabling just one target opts only that one in.
        autoexport.set_auto("flomo", True, self.cfg)
        self.assertEqual(autoexport.configured_targets(self.cfg), ["flomo"])

    def test_obsidian_autoexport_target(self):
        obs_dir = self.root / "obsidian_managed"
        save_config("export_obsidian_dir", str(obs_dir), self.cfg)
        autoexport.set_auto("obsidian", True, self.cfg)
        self.assertEqual(autoexport.configured_targets(self.cfg), ["obsidian"])
        results = self._run()
        self.assertEqual(results, [{"target": "obsidian", "status": "success", "count": 2}])
        self.assertEqual(sorted(p.name for p in obs_dir.glob("*.md")), ["书b1.md", "书b2.md"])
        # Second run with no changes writes 0 files
        results2 = self._run()
        self.assertEqual(results2, [{"target": "obsidian", "status": "success", "count": 0}])


if __name__ == "__main__":
    unittest.main()
