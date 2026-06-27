from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from weread_vault import sync_lock


class SyncLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "vault.db"

    def test_second_sync_is_skipped_while_first_holds_lock(self):
        with sync_lock.single_sync(self.db) as first:
            self.assertTrue(first)
            with sync_lock.single_sync(self.db) as second:
                self.assertFalse(second)  # the "both fire at 07:00" case: one runs, one skips

    def test_lock_is_released_and_reusable(self):
        with sync_lock.single_sync(self.db) as acquired:
            self.assertTrue(acquired)
        with sync_lock.single_sync(self.db) as again:
            self.assertTrue(again)


if __name__ == "__main__":
    unittest.main()
