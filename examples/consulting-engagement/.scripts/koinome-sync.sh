#!/bin/bash
# koinome-sync.sh: validated git synchronisation for a corpus folder.
# Portable: bash 3.2+ (macOS default /bin/bash).
# Delegates to koinome_sync.py for the state machine.

set -euo pipefail

CORPUS_ROOT="${1:-${CORPUS_ROOT:-$HOME/corpus}}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/koinome_sync.py" "$CORPUS_ROOT"
