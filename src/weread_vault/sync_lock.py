"""A cross-process advisory lock so two syncs never run against the same database at once.

Why this exists: a user can have both the built-in daily auto-sync (launchd / Task Scheduler /
cron) and an OpenClaw cron set to 07:00. Without a lock, two `weread-vault sync` processes would
hammer the same SQLite file concurrently and hit "database is locked" / do duplicate work. With
this lock the first one runs and the second one detects it and exits cleanly (it's a no-op, not
an error — the other process is already doing the sync).
"""

from __future__ import annotations

import contextlib
import os
import time
from collections.abc import Iterator
from pathlib import Path

_STALE_SECONDS = 3600  # a lock file older than this is assumed orphaned (crashed process)


@contextlib.contextmanager
def single_sync(db_path: Path) -> Iterator[bool]:
    """Yield True if we acquired the sync lock for ``db_path``, False if another sync holds it.

    Uses fcntl.flock where available (POSIX: macOS/Linux) — robust and auto-released if the
    process dies. Falls back to an atomic O_EXCL lock file with staleness on platforms without
    fcntl (Windows).
    """
    lock_path = Path(f"{db_path}.sync.lock")
    try:
        import fcntl
    except ImportError:
        fcntl = None

    if fcntl is not None:
        handle = open(lock_path, "w")  # noqa: SIM115 — kept open for the lock's lifetime
        try:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                yield False
                return
            handle.write(str(os.getpid()))
            handle.flush()
            yield True
        finally:
            with contextlib.suppress(OSError):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()
            with contextlib.suppress(OSError):
                lock_path.unlink()
        return

    # Windows / no fcntl: best-effort atomic lock file, reclaimed if clearly stale.
    if lock_path.exists() and time.time() - lock_path.stat().st_mtime > _STALE_SECONDS:
        with contextlib.suppress(OSError):
            lock_path.unlink()
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        yield False
        return
    try:
        os.write(fd, str(os.getpid()).encode("utf-8"))
        os.close(fd)
        yield True
    finally:
        with contextlib.suppress(OSError):
            lock_path.unlink()
