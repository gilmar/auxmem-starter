#!/bin/bash
# check_repo.sh: single local verification entry point for maintainers and CI.
# Covers Python tests, static checks, shell lint, package build, wheel smoke,
# manifest freshness, and scratch auxmem validation.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== sync dev dependencies =="
uv sync --group dev

echo "== ruff =="
uv run ruff check .

echo "== pytest =="
uv run pytest

echo "== shellcheck =="
bash scripts/lint-shell.sh

echo "== package build =="
uv build

echo "== wheel install smoke =="
bash scripts/smoke_install.sh

echo "== manifest freshness =="
uv run python build_manifest.py
git diff --exit-code -- auxmem/template/.auxmem-manifest.json

echo "check_repo.sh: all checks passed"
