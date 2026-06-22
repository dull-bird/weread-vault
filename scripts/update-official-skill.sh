#!/usr/bin/env bash
set -euo pipefail

git submodule update --init --remote vendor/tencent-weread-skill
git -C vendor/tencent-weread-skill log -1 --oneline
