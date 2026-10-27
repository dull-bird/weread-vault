#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

git submodule update --init --remote vendor/tencent-weread-skill
git -C vendor/tencent-weread-skill log -1 --oneline

# Keep the packaged fallback in sync with the vendored SKILL.md (runtime reads the vendored file
# directly; the fallback only matters for installs without the submodule, e.g. wheels).
version=$(awk -F: '/^---/{n++; next} n==1 && $1=="version"{gsub(/[ "\x27]/,"",$2); print $2; exit}' \
  vendor/tencent-weread-skill/skills/SKILL.md)
if [ -z "${version}" ]; then
  echo "未能从 vendor/tencent-weread-skill/skills/SKILL.md 读到 version，请手动检查。" >&2
  exit 1
fi
sed -i.bak -E "s/^SKILL_VERSION_FALLBACK = \"[^\"]*\"/SKILL_VERSION_FALLBACK = \"${version}\"/" src/weread_vault/config.py
rm -f src/weread_vault/config.py.bak
echo "官方 Skill 版本：${version}（已同步 SKILL_VERSION_FALLBACK）。"
echo "下一步：审阅 git -C vendor/tencent-weread-skill log -p 的接口变化，再跑 PYTHONPATH=src python3 -m pytest -q。"
