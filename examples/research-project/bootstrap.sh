#!/bin/bash
# bootstrap.sh: set up a corpus created from this template.
# Idempotent. Run from the corpus root: ./bootstrap.sh
#
# Options:
#   --refresh-skills   re-copy provider skill dirs that were copied (not symlinked)
#
# Does:
#   1. checks python + pyyaml (does not auto-install into system Python)
#   2. creates domain folders from .scripts/koinome.config.json
#   3. initializes git if needed
#   4. links provider skill dirs to .skills/
#   5. installs the pre-commit hook
#   6. generates MOCs
#   7. runs the validator
# Does NOT: set a git remote, install systemd sync (see docs/SETUP.md).

set -euo pipefail
cd "$(dirname "$0")"
CFG=".scripts/koinome.config.json"
REFRESH_SKILLS=0

while [ $# -gt 0 ]; do
    case "$1" in
        --refresh-skills) REFRESH_SKILLS=1; shift ;;
        -h|--help)
            echo "usage: ./bootstrap.sh [--refresh-skills]"
            exit 0
            ;;
        *)
            echo "unknown option: $1" >&2
            exit 1
            ;;
    esac
done

echo "== 1. dependencies =="
command -v python3 >/dev/null || { echo "python3 required" >&2; exit 1; }
if ! python3 -c "import yaml" 2>/dev/null; then
    cat <<'EOF' >&2
PyYAML is required but not available to this python3.

Bootstrap does not install packages into system Python automatically.
Use one of these supported paths:

  # Recommended: install Koinome (includes PyYAML)
  uv tool install koinome
  pipx install koinome

  # Or a project virtual environment
  python3 -m venv .venv
  source .venv/bin/activate   # Windows: .venv\Scripts\activate
  pip install pyyaml
  ./bootstrap.sh

  # Or use a venv only for validator/MOC scripts
  python3 -m venv .venv && source .venv/bin/activate && pip install pyyaml

Then re-run: ./bootstrap.sh
EOF
    exit 1
fi
echo "ok"

if [ "$REFRESH_SKILLS" = "1" ]; then
    echo "== refresh copied provider skills =="
    if [ -f .koinome/skills-copies ]; then
        refreshed=0
        while IFS= read -r provider_dir || [ -n "${provider_dir:-}" ]; do
            [ -z "$provider_dir" ] && continue
            if [ -L "$provider_dir" ]; then
                echo "  $provider_dir is a symlink; nothing to refresh"
                continue
            fi
            if [ ! -d "$provider_dir" ]; then
                echo "  $provider_dir missing; skipping"
                continue
            fi
            rm -rf "$provider_dir"
            cp -R .skills "$provider_dir"
            echo "  refreshed $provider_dir from .skills (copy)"
            refreshed=1
        done < .koinome/skills-copies
        if [ "$refreshed" = "0" ]; then
            echo "  no copied skill directories were refreshed"
        fi
    else
        echo "  no .koinome/skills-copies (provider dirs were symlinked or not yet bootstrapped)"
    fi
    echo ""
    echo "Skill refresh complete. Re-run ./bootstrap.sh without --refresh-skills for a full pass."
    exit 0
fi

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
mkdir -p .koinome
SKILLS_COPIES=".koinome/skills-copies"
touch "$SKILLS_COPIES"
record_skill_copy() {
    local provider_dir="$1"
    if ! grep -qxF "$provider_dir" "$SKILLS_COPIES" 2>/dev/null; then
        echo "$provider_dir" >> "$SKILLS_COPIES"
    fi
}
remove_skill_copy_record() {
    local provider_dir="$1"
    if [ -f "$SKILLS_COPIES" ]; then
        grep -vxF "$provider_dir" "$SKILLS_COPIES" > "${SKILLS_COPIES}.tmp" || true
        mv "${SKILLS_COPIES}.tmp" "$SKILLS_COPIES"
    fi
}
link_skills() {
    local provider_dir="$1"
    local parent
    parent="$(dirname "$provider_dir")"
    mkdir -p "$parent"
    if [ -L "$provider_dir" ]; then
        echo "  $provider_dir already linked"
        remove_skill_copy_record "$provider_dir"
        return
    fi
    if [ -e "$provider_dir" ]; then
        echo "  $provider_dir exists (not a symlink); skipping to avoid overwriting user content"
        return
    fi
    if ln -s ../.skills "$provider_dir" 2>/dev/null; then
        echo "  linked $provider_dir -> ../.skills"
        remove_skill_copy_record "$provider_dir"
    else
        cp -R .skills "$provider_dir"
        record_skill_copy "$provider_dir"
        echo "  copied .skills -> $provider_dir (symlink unavailable; run ./bootstrap.sh --refresh-skills after skill updates)"
    fi
}
link_skills .claude/skills
link_skills .codex/skills
link_skills .gemini/skills
link_skills .cursor/skills

echo "== 5. pre-commit hook =="
cp .scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "  installed (re-run ./bootstrap.sh after koinome upgrade to refresh the hook)"

echo "== 6. generate MOCs =="
if python3 - "$CFG" << 'PY'
import json, sys
cfg = json.load(open(sys.argv[1]))
sys.exit(0 if cfg.get("domains") else 1)
PY
then
  python3 .scripts/gen_mocs.py
else
  echo "  skipped (no domains yet; run the koinome-init skill first)"
fi

echo "== 7. validate =="
if python3 - "$CFG" << 'PY'
import json, sys
cfg = json.load(open(sys.argv[1]))
sys.exit(0 if cfg.get("domains") else 1)
PY
then
  if python3 .scripts/validate_corpus.py --all; then
    echo ""
    echo "Bootstrap complete. Next steps (see docs/SETUP.md):"
    echo "  - set your git remote and push"
    echo "  - optional: install the sync timer (.scripts/koinome-sync.systemd)"
    echo "  - seed the corpus from provider exports (docs/IMPORTING.md)"
  else
    echo "validation reported issues above; fix them, then re-run."
    exit 1
  fi
else
  echo "  skipped (no domains yet; run the koinome-init skill first)"
  echo ""
  echo "Bootstrap complete. Next steps:"
  echo "  - point your agent at this corpus and run the koinome-init skill"
  echo "  - then set your git remote and push (see docs/SETUP.md)"
fi
