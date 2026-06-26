"""Register a daily auto-sync with the OS scheduler (launchd / Task Scheduler / cron).

We deliberately do NOT run a long-lived daemon. The OS scheduler wakes `weread-vault`
once a day, it syncs and exits — robust across reboots, no resident process, no extra deps.

The pure builders (`launchd_plist`, `cron_line`, `schtasks_create_args`, `sync_command`) are
platform-independent so they can be unit-tested on any runner; `install`/`remove`/`status`
dispatch by platform and only touch the system when ``activate=True``.
"""

from __future__ import annotations

import platform
import plistlib
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

LABEL = "com.weread-vault.sync"


def parse_time(value: str) -> tuple[int, int]:
    parts = value.strip().split(":")
    if len(parts) != 2 or not (parts[0].isdigit() and parts[1].isdigit()):
        raise ValueError(f"时间格式应为 HH:MM，比如 07:00（收到：{value}）")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"时间超出范围：{value}")
    return hour, minute


def _executable() -> str:
    """The shell-quoted command used to invoke weread-vault from a scheduled job."""
    if getattr(sys, "frozen", False):
        return shlex.quote(sys.executable)
    found = shutil.which("weread-vault")
    if found:
        return shlex.quote(found)
    return f"{shlex.quote(sys.executable)} -m weread_vault"


def sync_command(db: str | None = None, export: str | None = None, exe: str | None = None) -> str:
    exe = exe or _executable()
    db_part = f" --db {shlex.quote(db)}" if db else ""
    command = f"{exe}{db_part} sync"
    if export:
        command += f" && {exe}{db_part} export markdown --out {shlex.quote(export)}"
    return command


# ---------- macOS: launchd ----------
def launchd_plist(hour: int, minute: int, command: str) -> bytes:
    return plistlib.dumps({
        "Label": LABEL,
        "ProgramArguments": ["/bin/sh", "-lc", command],
        "StartCalendarInterval": {"Hour": hour, "Minute": minute},
        "RunAtLoad": False,
    })


def launchd_path(agents_dir: Path | None = None) -> Path:
    return (agents_dir or (Path.home() / "Library" / "LaunchAgents")) / f"{LABEL}.plist"


# ---------- Linux: cron ----------
def cron_line(hour: int, minute: int, command: str) -> str:
    return f"{minute} {hour} * * * {command}  # {LABEL}"


def _read_crontab() -> str:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else ""


def _write_crontab(text: str) -> None:
    subprocess.run(["crontab", "-"], input=text, text=True, check=True)


def _crontab_without_label(text: str) -> list[str]:
    return [line for line in text.splitlines() if LABEL not in line]


# ---------- Windows: Task Scheduler ----------
def schtasks_create_args(hour: int, minute: int, command: str) -> list[str]:
    return ["schtasks", "/create", "/tn", LABEL, "/sc", "daily",
            "/st", f"{hour:02d}:{minute:02d}", "/tr", f'cmd /c "{command}"', "/f"]


# ---------- dispatch ----------
def install(hour: int, minute: int, db: str | None = None, export: str | None = None,
            *, agents_dir: Path | None = None, activate: bool = True) -> dict[str, object]:
    command = sync_command(db, export)
    system = platform.system()
    if system == "Darwin":
        path = launchd_path(agents_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(launchd_plist(hour, minute, command))
        if activate:
            subprocess.run(["launchctl", "unload", str(path)], capture_output=True)
            subprocess.run(["launchctl", "load", str(path)], capture_output=True)
        return {"platform": "macOS · launchd", "path": str(path), "command": command}
    if system == "Windows":
        args = schtasks_create_args(hour, minute, command)
        if activate:
            subprocess.run(args, capture_output=True, check=True)
        return {"platform": "Windows · 任务计划", "task": LABEL, "command": command}
    line = cron_line(hour, minute, command)
    if activate:
        _write_crontab("\n".join([*_crontab_without_label(_read_crontab()), line, ""]))
    return {"platform": "Linux · cron", "line": line, "command": command}


def remove(*, agents_dir: Path | None = None, activate: bool = True) -> bool:
    system = platform.system()
    if system == "Darwin":
        path = launchd_path(agents_dir)
        if not path.exists():
            return False
        if activate:
            subprocess.run(["launchctl", "unload", str(path)], capture_output=True)
        path.unlink()
        return True
    if system == "Windows":
        if activate:
            subprocess.run(["schtasks", "/delete", "/tn", LABEL, "/f"], capture_output=True)
        return True
    current = _read_crontab()
    if LABEL not in current:
        return False
    if activate:
        _write_crontab("\n".join([*_crontab_without_label(current), ""]))
    return True


def status(*, agents_dir: Path | None = None) -> dict[str, object]:
    system = platform.system()
    if system == "Darwin":
        path = launchd_path(agents_dir)
        return {"enabled": path.exists(), "platform": "macOS · launchd", "path": str(path)}
    if system == "Windows":
        result = subprocess.run(["schtasks", "/query", "/tn", LABEL], capture_output=True)
        return {"enabled": result.returncode == 0, "platform": "Windows · 任务计划"}
    return {"enabled": LABEL in _read_crontab(), "platform": "Linux · cron"}
