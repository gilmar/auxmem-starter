#!/bin/bash
# auxmem-sync.sh: validated git synchronisation for an auxmem folder.
# Portable: bash 3.2+ (macOS default /bin/bash).
# Delegates to auxmem_sync.py for the state machine.

set -euo pipefail

AUXMEM="${1:-${AUXMEM:-$HOME/auxmem}}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/auxmem_sync.py" "$AUXMEM"
