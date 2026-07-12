#!/bin/bash
# compatibility_smoke.sh: reproducible smoke referenced by docs/COMPATIBILITY.md.
# Verifies scaffold, validation, conformance, and upgrade dry-run without agent CLIs.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== compatibility smoke: fresh scaffold =="
uv run python -m koinome.release_check --scaffold-smoke

echo "== compatibility smoke: wheel install =="
bash scripts/smoke_install.sh

echo "compatibility_smoke.sh: deterministic checks passed"
echo "Agent provider smokes (Claude Code, Codex, Gemini, Cursor) are manual — see docs/COMPATIBILITY.md"
