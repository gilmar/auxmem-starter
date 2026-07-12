#!/bin/bash
# smoke_install.sh: install the built wheel in a temp venv and run auxmem new.
# Expects `uv build` to have produced dist/auxmem-*.whl in the repo root.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DIST="$ROOT/dist"
WHEEL="$(ls -t "$DIST"/auxmem-*.whl 2>/dev/null | head -1 || true)"
if [ -z "$WHEEL" ]; then
    echo "no wheel found in $DIST; run uv build first" >&2
    exit 1
fi

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/auxmem-smoke.XXXXXX")"
trap 'rm -rf "$WORKDIR"' EXIT

VENV="$WORKDIR/venv"
DEST="$WORKDIR/auxmem"
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --quiet "$WHEEL"

auxmem new --name smoke --path "$DEST" --domain 10-projects=projects
python "$DEST/.scripts/validate_auxmem.py" --all

echo "smoke_install.sh: wheel install and auxmem new succeeded"
