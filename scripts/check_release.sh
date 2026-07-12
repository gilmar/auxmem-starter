#!/bin/bash
# check_release.sh: P0 release gate — full repo checks plus version/compatibility discipline.
#
# Usage:
#   bash scripts/check_release.sh
#   bash scripts/check_release.sh --target-version 0.1.0rc1
#
# Set ALLOW_DIRTY_TREE=1 to skip the clean-tree requirement (local dev only).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TARGET_VERSION=""
if [ "${1:-}" = "--target-version" ]; then
    TARGET_VERSION="${2:?usage: check_release.sh [--target-version VERSION]}"
fi

if [ "${ALLOW_DIRTY_TREE:-}" != "1" ]; then
    if [ -n "$(git status --porcelain)" ]; then
        echo "check_release.sh: working tree must be clean (or set ALLOW_DIRTY_TREE=1)" >&2
        exit 1
    fi
fi

echo "== repository checks =="
bash scripts/check_repo.sh

echo "== release discipline =="
RELEASE_ARGS=(--strict)
if [ "${ALLOW_DIRTY_TREE:-}" != "1" ]; then
    RELEASE_ARGS+=(--require-clean-tree)
fi
if [ -n "$TARGET_VERSION" ]; then
    RELEASE_ARGS+=(--target-version "$TARGET_VERSION")
fi
uv run python -m koinome.release_check "${RELEASE_ARGS[@]}"

echo "== compatibility smoke =="
bash scripts/compatibility_smoke.sh

echo "== reference corpus evaluation =="
uv run python -m koinome.evaluation

echo "check_release.sh: all release checks passed"
