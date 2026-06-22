from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from .config import GATEWAY_URL, SKILL_VERSION
from .errors import GatewayError, SkillUpgradeRequired


class Gateway:
    """Small, dependency-free client for the WeRead Agent gateway."""

    def __init__(self, api_key: str | None = None, sleep_seconds: float = 0.35):
        self.api_key = api_key or os.environ.get("WEREAD_API_KEY", "")
        self.sleep_seconds = sleep_seconds

    def call(self, api_name: str, **params: Any) -> dict[str, Any]:
        if not self.api_key:
            raise GatewayError("未设置 WEREAD_API_KEY。仅同步需要它；查看本地数据不需要。")
        payload = {"api_name": api_name, "skill_version": SKILL_VERSION, **params}
        request = urllib.request.Request(
            GATEWAY_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        last_error: object = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    result = json.loads(response.read().decode("utf-8"))
                if result.get("upgrade_info"):
                    message = result["upgrade_info"].get("message", "请升级微信读书 Skill")
                    raise SkillUpgradeRequired(message)
                if result.get("errcode", 0) == 0:
                    return result
                last_error = result.get("errmsg") or result
            except SkillUpgradeRequired:
                raise
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
                last_error = error
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1))
        raise GatewayError(f"{api_name} 调用失败（已重试 4 次）：{last_error}")
