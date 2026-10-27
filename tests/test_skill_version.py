from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from weread_vault import config
from weread_vault.gateway import _upgrade_message


class SkillVersionTests(unittest.TestCase):
    def test_reads_version_from_vendored_skill(self):
        if not config.OFFICIAL_SKILL_MD.exists():
            self.skipTest("vendor submodule not checked out")
        self.assertEqual(config.SKILL_VERSION, config.official_skill_version())
        # The packaged fallback must match the vendored protocol version.
        self.assertEqual(config.SKILL_VERSION_FALLBACK, config.official_skill_version())

    def test_parses_front_matter_and_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "SKILL.md"
            md.write_text("---\nname: x\nversion: '9.8.7'\n---\n# body\nversion: 0\n", encoding="utf-8")
            self.assertEqual(config.official_skill_version(md), "9.8.7")
            md.write_text("# no front matter\n", encoding="utf-8")
            self.assertEqual(config.official_skill_version(md, fallback="1.2.3"), "1.2.3")
            self.assertEqual(config.official_skill_version(Path(tmp) / "missing.md", fallback="1.2.3"), "1.2.3")

    def test_upgrade_message_points_to_weread_vault_update(self):
        message = _upgrade_message({"message": "请升级到 1.0.6"})
        self.assertIn("weread-vault update", message)
        self.assertIn("请升级到 1.0.6", message)
        self.assertIn(config.SKILL_VERSION, message)


if __name__ == "__main__":
    unittest.main()
