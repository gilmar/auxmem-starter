#!/bin/bash
# smoke_install.sh: install the built wheel in a temp venv and run koinome new.
# Expects `uv build` to have produced dist/koinome-*.whl in the repo root.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DIST="$ROOT/dist"
WHEEL="$(ls -t "$DIST"/koinome-*.whl 2>/dev/null | head -1 || true)"
if [ -z "$WHEEL" ]; then
    echo "no wheel found in $DIST; run uv build first" >&2
    exit 1
fi

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/corpus-smoke.XXXXXX")"
trap 'rm -rf "$WORKDIR"' EXIT

VENV="$WORKDIR/venv"
DEST="$WORKDIR/corpus"
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --quiet "$WHEEL"

koinome new --name smoke --path "$DEST" --domain 10-projects=projects
python "$DEST/.scripts/validate_corpus.py" --all

DEST_SPACE="$WORKDIR/my corpus"
koinome new --name smoke-space --path "$DEST_SPACE" --domain 10-projects=projects
python "$DEST_SPACE/.scripts/validate_corpus.py" --all

echo "smoke_install.sh: wheel install and koinome new succeeded"
