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
                    message = result["upgrade_info"].get("message", "请升级微信读书 Skill")
                    raise SkillUpgradeRequired(message)
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
            # Some Linux builds provide Python without the _ssl extension. urllib then
            # reports HTTPS as an unknown URL type even though the OS has a TLS-capable curl.
            if "unknown url type: https" not in str(error).lower():
                raise
            return self._post_with_curl(payload)

    def _post_with_curl(self, payload: dict[str, Any]) -> dict[str, Any]:
        curl = shutil.which("curl")
        if not curl:
            raise GatewayError("当前 Python 不支持 HTTPS，且未找到 curl；请安装带 SSL 的 Python 或 curl。")
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
