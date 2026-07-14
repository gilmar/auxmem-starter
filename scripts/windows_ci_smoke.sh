#!/bin/bash
# windows_ci_smoke.sh: Git Bash smoke for Windows runners (issue #36).
# Asserts koinome new + bootstrap succeed and shell scripts stay LF-only.
#
# Usage (Git Bash / WSL):
#   bash scripts/windows_ci_smoke.sh
#   DEST=/tmp/win-smoke bash scripts/windows_ci_smoke.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DEST="${DEST:-${RUNNER_TEMP:-/tmp}/koinome-windows-ci-smoke}"
rm -rf "$DEST"

echo "== sync =="
uv sync --group dev

echo "== line-ending and bootstrap tests =="
uv run pytest tests/test_line_endings.py tests/test_bootstrap.py tests/test_scaffold_validation.py -q

echo "== koinome new smoke =="
uv run koinome new \
  --name windows-ci \
  --path "$DEST" \
  --domain 10-projects=projects

echo "== assert LF-only bash scripts =="
uv run python - "$DEST" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [root / "bootstrap.sh", root / ".scripts" / "pre-commit", *sorted((root / ".scripts").glob("*.sh"))]
hook = root / ".git" / "hooks" / "pre-commit"
if hook.is_file():
    paths.append(hook)
offenders = [str(p.relative_to(root)) for p in paths if p.is_file() and b"\r" in p.read_bytes()]
if offenders:
    raise SystemExit(f"CRLF remains in: {', '.join(offenders)}")
print(f"ok: {len(paths)} script(s) are LF-only")
PY

echo "== assert gitattributes force LF =="
grep -q "eol=lf" "$DEST/.gitattributes"
grep -Fq "*.sh" "$DEST/.gitattributes"

echo "windows_ci_smoke.sh: passed"
