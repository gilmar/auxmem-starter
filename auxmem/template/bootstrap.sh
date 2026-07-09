#!/bin/bash
# bootstrap.sh: set up a vault created from this template.
# Idempotent. Run from the vault root: ./bootstrap.sh
#
# Does:
#   1. checks python + pyyaml
#   2. creates domain folders from .scripts/vault.config.json
#   3. initializes git if needed
#   4. links provider skill dirs to .skills/
#   5. installs the pre-commit hook
#   6. generates MOCs
#   7. runs the validator
# Does NOT: set a git remote, install systemd sync (see docs/SETUP.md).

set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
CFG=".scripts/vault.config.json"

echo "== 1. dependencies =="
command -v python3 >/dev/null || { echo "python3 required"; exit 1; }
python3 -c "import yaml" 2>/dev/null || {
    echo "installing pyyaml..."
    pip install pyyaml --quiet --break-system-packages 2>/dev/null || pip install pyyaml --quiet
}
echo "ok"

echo "== 2. domain folders from config =="
python3 - "$CFG" << 'PY'
import json, sys, pathlib
cfg = json.load(open(sys.argv[1]))
folders = list(cfg["domains"].keys()) + cfg.get("structural_folders", [])
for f in folders:
    p = pathlib.Path(f)
    p.mkdir(parents=True, exist_ok=True)
    keep = p / ".gitkeep"
    if not any(p.iterdir()):
        keep.touch()
    print(f"  {f}")
PY

echo "== 3. git =="
if [ ! -d .git ]; then
    git init -q
    echo "  initialized empty repo"
else
    echo "  repo exists"
fi

echo "== 4. provider skill symlinks =="
link_skills() {
    local provider_dir="$1"
    local parent
    parent="$(dirname "$provider_dir")"
    mkdir -p "$parent"
    if [ -L "$provider_dir" ]; then
        echo "  $provider_dir already linked"
        return
    fi
    if [ -e "$provider_dir" ]; then
        echo "  $provider_dir exists (not a symlink); skipping"
        return
    fi
    if ln -s ../.skills "$provider_dir" 2>/dev/null; then
        echo "  linked $provider_dir -> ../.skills"
    else
        cp -R .skills "$provider_dir"
        echo "  copied .skills -> $provider_dir (symlink unavailable)"
    fi
}
link_skills .claude/skills
link_skills .codex/skills
link_skills .gemini/skills
link_skills .cursor/skills

echo "== 5. pre-commit hook =="
cp .scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "  installed"

echo "== 6. generate MOCs =="
python3 .scripts/gen_mocs.py

echo "== 7. validate =="
if python3 .scripts/validate_vault.py --all; then
    echo ""
    echo "Bootstrap complete. Next steps (see docs/SETUP.md):"
    echo "  - set your git remote and push"
    echo "  - optional: install the sync timer (.scripts/vault-sync.systemd)"
    echo "  - seed the vault from provider exports (docs/IMPORTING.md)"
else
    echo "validation reported issues above; fix them, then re-run."
    exit 1
fi
