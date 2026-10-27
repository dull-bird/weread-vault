from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from typing import Any

from .config import GATEWAY_URL, SKILL_VERSION, read_api_key
from .errors import GatewayError, SkillUpgradeRequired


class Gateway:
    """Small, dependency-free client for the WeRead Agent gateway."""

    def __init__(self, api_key: str | None = None, sleep_seconds: float = 0.15):
        self.api_key = api_key or read_api_key()
        self.sleep_seconds = sleep_seconds

    def call(self, api_name: str, **params: Any) -> dict[str, Any]:
        if not self.api_key:
            raise GatewayError("未设置 WEREAD_API_KEY。仅同步需要它；查看本地数据不需要。")
        payload = {"api_name": api_name, "skill_version": SKILL_VERSION, **params}
        last_error: object = None
        for attempt in range(4):
            try:
                result = self._post(payload)
                if result.get("upgrade_info"):
                    raise SkillUpgradeRequired(_upgrade_message(result["upgrade_info"]))
                if result.get("errcode", 0) == 0:
                    return result
                last_error = result.get("errmsg") or result
            except SkillUpgradeRequired:
                raise
            except GatewayError as error:
                last_error = error
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
                last_error = error
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1))
        raise GatewayError(f"{api_name} 调用失败（已重试 4 次）：{last_error}")

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            GATEWAY_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as error:
            if not _can_retry_with_curl(error):
                raise
            return self._post_with_curl(payload)

    def _post_with_curl(self, payload: dict[str, Any]) -> dict[str, Any]:
        curl = shutil.which("curl")
        if not curl:
            raise GatewayError("当前 Python HTTPS/证书环境不可用，且未找到 curl；请安装带 SSL 证书的 Python 或 curl。")
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as body_file:
            body_file.write(json.dumps(payload, ensure_ascii=False))
            body_path = body_file.name
        try:
            def quoted(value: str) -> str:
                return value.replace("\\", "\\\\").replace('"', '\\"')

            config = "\n".join(
                [
                    f'url = "{GATEWAY_URL}"',
                    'request = "POST"',
                    f'header = "Authorization: Bearer {quoted(self.api_key)}"',
                    'header = "Content-Type: application/json"',
                    f'data-binary = "@{quoted(body_path)}"',
                ]
            )
            result = subprocess.run(
                [curl, "--config", "-", "--fail", "--silent", "--show-error", "--max-time", "30"],
                input=config,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                raise GatewayError(f"curl 请求失败：{result.stderr.strip() or result.returncode}")
            return json.loads(result.stdout)
        finally:
            try:
                os.unlink(body_path)
            except OSError:
                pass


def _can_retry_with_curl(error: BaseException) -> bool:
    detail = str(error).lower()
    # Some Linux builds provide Python without the _ssl extension. urllib then
    # reports HTTPS as an unknown URL type even though the OS has a TLS-capable curl.
    if "unknown url type: https" in detail:
        return True
    # PyInstaller / embedded Python builds can have a working _ssl module but no
    # usable CA bundle. curl often still verifies successfully via the OS trust store.
    return "certificate_verify_failed" in detail


def _upgrade_message(info: object) -> str:
    """Turn the gateway's ``upgrade_info`` into advice that fits weread-vault users.

    The official message tells an agent to re-install the Skill; for weread-vault the fix is to
    upgrade weread-vault itself (which bundles the official protocol version).
    """
    upstream = ""
    if isinstance(info, dict):
        upstream = str(info.get("message") or "").strip()
        latest = info.get("latest_version") or info.get("version") or info.get("new_version")
    else:
        upstream = str(info or "").strip()
        latest = None
    lines = [
        f"微信读书接口要求更新官方 Skill 协议（weread-vault 当前上报 skill_version={SKILL_VERSION}"
        + (f"，最新 {latest}" if latest else "")
        + "）。",
        "请升级 weread-vault：运行 `weread-vault update`，或从源码 `git pull --recurse-submodules` 后重新安装；",
        "开发者可运行 scripts/update-official-skill.sh 升级 vendor 子模块并跑测试。",
    ]
    if upstream:
        lines.append(f"官方提示：{upstream}")
    return "\n".join(lines)
