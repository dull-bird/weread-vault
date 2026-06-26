from __future__ import annotations

import os
import sys
import json
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


def default_config_path() -> Path:
    return default_data_dir() / "config.json"


def _read_config(path: Path | None = None) -> dict[str, str]:
    config_path = path or default_config_path()
    if not config_path.exists():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def saved_api_key(path: Path | None = None) -> str:
    value = _read_config(path).get("weread_api_key", "")
    return value if isinstance(value, str) else ""


def api_key_source(path: Path | None = None) -> str:
    if os.environ.get("WEREAD_API_KEY"):
        return "env"
    if saved_api_key(path):
        return "config"
    return "none"


def read_api_key(path: Path | None = None) -> str:
    return os.environ.get("WEREAD_API_KEY") or saved_api_key(path)


def save_api_key(api_key: str, path: Path | None = None) -> Path:
    api_key = api_key.strip()
    if not api_key:
        raise ValueError("API Key 不能为空。")
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = _read_config(config_path)
    data["weread_api_key"] = api_key
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        config_path.chmod(0o600)
    except OSError:
        pass
    return config_path


def clear_api_key(path: Path | None = None) -> None:
    config_path = path or default_config_path()
    data = _read_config(config_path)
    if data.pop("weread_api_key", None) is None:
        return
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_config(key: str, path: Path | None = None) -> str:
    """Read an arbitrary saved value (e.g. flomo webhook, Notion token, last export dir)."""
    return str(_read_config(path).get(key, ""))


def save_config(key: str, value: str, path: Path | None = None) -> Path:
    """Persist (or, if value is empty, remove) an arbitrary config value with 0600 perms."""
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = _read_config(config_path)
    if value:
        data[key] = value
    else:
        data.pop(key, None)
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        config_path.chmod(0o600)
    except OSError:
        pass
    return config_path
