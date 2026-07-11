#!/bin/bash
# export_obsidian.sh: stage 1 of the Obsidian import pipeline.
# Runs obsidian-export to convert the vault to CommonMark, capturing its
# unresolved-link warnings for the restructure report.
#
# Usage: export_obsidian.sh <obsidian_vault> <export_dir>

set -euo pipefail

SRC="${1:?usage: export_obsidian.sh <obsidian_vault> <export_dir>}"
OUT="${2:?usage: export_obsidian.sh <obsidian_vault> <export_dir>}"

if ! command -v obsidian-export >/dev/null; then
    cat >&2 << 'EOF'
obsidian-export not found. Install one of:
  cargo install obsidian-export --locked            # needs Rust >= 1.85 (rustup)
  cargo install obsidian-export --version 23.12.0 --locked   # works on Rust 1.75 (Ubuntu 24 apt cargo)
  or download a release binary: https://github.com/zoni/obsidian-export/releases
EOF
    exit 1
fi

# default ignore file if the auxmem has none; gitignore syntax
if [ ! -f "$SRC/.export-ignore" ]; then
    printf '.obsidian/\n.trash/\nTemplates/\n' > "$SRC/.export-ignore"
    echo "wrote default $SRC/.export-ignore (edit and re-run if needed)"
fi

rm -rf "$OUT" && mkdir -p "$OUT"
obsidian-export "$SRC" "$OUT" 2> "$OUT/.export-warnings.txt" || {
    cat "$OUT/.export-warnings.txt" >&2
    exit 1
}

WARN=$(grep -c "Unable to find" "$OUT/.export-warnings.txt" 2>/dev/null || true)
echo "exported to $OUT (${WARN:-0} unresolved-link warning(s) captured)"
echo "next: python3 restructure_export.py --src $OUT --dst ~/auxmem --map map.json"
