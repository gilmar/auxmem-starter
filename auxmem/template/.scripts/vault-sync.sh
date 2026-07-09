#!/bin/bash
# vault-sync.sh: transparent git synchronisation for the vault.
# Safe to run concurrently (flock), from a systemd timer, or manually.
# Design: sync is unconditional. Validation is enforced by agents' own
# commits (pre-commit hook) and by CI, never by this script.
#
# Usage: vault-sync.sh [vault_path]   (default: $HOME/vault)

set -uo pipefail

VAULT="${1:-$HOME/vault}"
BRANCH="main"
REMOTE="origin"
HOST="$(hostname -s)"
LOCK="/tmp/vault-sync.lock"

log() { echo "[vault-sync $(date -Iseconds)] $*"; }

exec 9>"$LOCK"
flock -n 9 || { log "another sync is running, skipping"; exit 0; }

cd "$VAULT" || { log "vault not found: $VAULT"; exit 1; }

# 1. Commit local changes, bypassing the validation hook.
#    VAULT_AUTOSYNC=1 lets the pre-commit hook distinguish sync commits
#    from agent/human commits if you prefer that over --no-verify.
if [ -n "$(git status --porcelain)" ]; then
    git add -A
    VAULT_AUTOSYNC=1 git commit --no-verify -q \
        -m "sync($HOST): $(date -Iseconds)" || true
fi

# 2. Pull with rebase + autostash.
if ! git pull --rebase --autostash -q "$REMOTE" "$BRANCH" 2>/dev/null; then
    log "rebase conflict, taking the escape hatch"
    git rebase --abort 2>/dev/null || true

    CONFLICT_BRANCH="sync-conflict/${HOST}-$(date +%Y%m%d-%H%M%S)"
    git branch "$CONFLICT_BRANCH"
    git push -q "$REMOTE" "$CONFLICT_BRANCH"

    # reset local main to remote so sync keeps working
    git fetch -q "$REMOTE" "$BRANCH"
    git reset --hard -q "$REMOTE/$BRANCH"

    # leave a machine-and-human-readable alert in the inbox
    ALERT="00-inbox/sync-conflict-$(date +%Y%m%d-%H%M%S).md"
    cat > "$ALERT" << EOF
---
title: Sync conflict on $HOST
summary: Automatic sync hit a rebase conflict. Local state was preserved on branch $CONFLICT_BRANCH and local main was reset to remote. Merge the branch to recover local edits.
type: log
status: active
domain: governance
created: $(date +%F)
updated: $(date +%F)
---
Resolve with: git merge $CONFLICT_BRANCH (or cherry-pick), then delete the branch.
EOF
    git add "$ALERT"
    VAULT_AUTOSYNC=1 git commit --no-verify -q -m "sync($HOST): conflict alert"
fi

# 3. Push. One retry after re-pulling, in case the remote moved mid-run.
if ! git push -q "$REMOTE" "$BRANCH" 2>/dev/null; then
    git pull --rebase --autostash -q "$REMOTE" "$BRANCH" 2>/dev/null || true
    git push -q "$REMOTE" "$BRANCH" || { log "push failed, will retry next cycle"; exit 0; }
fi

log "ok"
