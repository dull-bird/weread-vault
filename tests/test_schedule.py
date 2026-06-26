from __future__ import annotations

import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from weread_vault import schedule as s


class ScheduleTests(unittest.TestCase):
    def test_parse_time(self):
        self.assertEqual(s.parse_time("07:00"), (7, 0))
        self.assertEqual(s.parse_time("23:59"), (23, 59))
        for bad in ("7am", "25:00", "12:60", "noon"):
            with self.assertRaises(ValueError):
                s.parse_time(bad)

    def test_sync_command_quotes_and_chains_export(self):
        self.assertEqual(s.sync_command(exe="weread-vault"), "weread-vault sync")
        cmd = s.sync_command(db="/tmp/a b.db", export="/out dir", exe="weread-vault")
        self.assertIn("--db '/tmp/a b.db' sync", cmd)
        self.assertIn(" && ", cmd)
        self.assertIn("export markdown --out '/out dir'", cmd)

    def test_launchd_plist(self):
        data = plistlib.loads(s.launchd_plist(7, 30, "weread-vault sync"))
        self.assertEqual(data["Label"], s.LABEL)
        self.assertEqual(data["StartCalendarInterval"], {"Hour": 7, "Minute": 30})
        self.assertEqual(data["ProgramArguments"][:2], ["/bin/sh", "-lc"])
        self.assertIn("weread-vault sync", data["ProgramArguments"][-1])

    def test_cron_line(self):
        self.assertEqual(s.cron_line(7, 5, "X"), f"5 7 * * * X  # {s.LABEL}")

    def test_crontab_without_label_drops_our_lines(self):
        text = f"0 1 * * * other\n5 7 * * * X  # {s.LABEL}\n0 2 * * * keep"
        self.assertEqual(s._crontab_without_label(text), ["0 1 * * * other", "0 2 * * * keep"])

    def test_schtasks_args(self):
        args = s.schtasks_create_args(7, 5, "weread-vault sync")
        self.assertEqual(args[:3], ["schtasks", "/create", "/tn"])
        self.assertIn(s.LABEL, args)
        self.assertIn("07:05", args)

    # install() dispatches by OS — exercise all three branches on any host via mock, activate=False
    def test_install_macos_writes_plist(self):
        with mock.patch.object(s.platform, "system", return_value="Darwin"), tempfile.TemporaryDirectory() as tmp:
            info = s.install(7, 0, db="/tmp/x.db", agents_dir=Path(tmp), activate=False)
            path = Path(str(info["path"]))
            self.assertTrue(path.exists())
            self.assertEqual(plistlib.loads(path.read_bytes())["Label"], s.LABEL)

    def test_install_windows_builds_task(self):
        with mock.patch.object(s.platform, "system", return_value="Windows"):
            info = s.install(7, 0, activate=False)
            self.assertEqual(info["task"], s.LABEL)
            self.assertIn("sync", str(info["command"]))

    def test_install_linux_builds_cron_line(self):
        with mock.patch.object(s.platform, "system", return_value="Linux"):
            info = s.install(7, 0, activate=False)
            self.assertIn(s.LABEL, str(info["line"]))

    def test_status_macos_reflects_plist_presence(self):
        with mock.patch.object(s.platform, "system", return_value="Darwin"), tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp)
            self.assertFalse(s.status(agents_dir=agents)["enabled"])
            s.install(7, 0, agents_dir=agents, activate=False)
            self.assertTrue(s.status(agents_dir=agents)["enabled"])


if __name__ == "__main__":
    unittest.main()
