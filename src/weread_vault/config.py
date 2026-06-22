from __future__ import annotations

import os
import sys
from pathlib import Path


DEFAULT_PORT = 8765
GATEWAY_URL = "https://i.weread.qq.com/api/agent/gateway"
SKILL_VERSION = "1.0.3"


def default_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "weread-vault"
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "weread-vault"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "weread-vault"


def default_db_path() -> Path:
    return default_data_dir() / "weread-vault.db"
