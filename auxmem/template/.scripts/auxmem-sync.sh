#!/bin/bash
# auxmem-sync.sh: transparent git synchronisation for an auxmem folder.
# Safe to run concurrently (mkdir lock), from a systemd timer, or manually.
# Portable: bash 3.2+ (macOS default /bin/bash).

set -uo pipefail

AUXMEM="${1:-$HOME/auxmem}"
BRANCH="main"
REMOTE="origin"
LOCK_DIR="/tmp/auxmem-sync.lock.d"

iso_now() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}

short_host() {
    if hostname -s >/dev/null 2>&1; then
        hostname -s
    else
        hostname 2>/dev/null | cut -d. -f1
    fi
}

HOST="$(short_host)"

log() { echo "[auxmem-sync $(iso_now)] $*"; }

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    log "another sync is running, skipping"
    exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

cd "$AUXMEM" || { log "auxmem folder not found: $AUXMEM"; exit 1; }

if [ -n "$(git status --porcelain)" ]; then
    git add -A
    AUXMEM_AUTOSYNC=1 git commit --no-verify -q \
        -m "sync($HOST): $(iso_now)" || true
fi

if ! git pull --rebase --autostash -q "$REMOTE" "$BRANCH" 2>/dev/null; then
    log "rebase conflict, taking the escape hatch"
    git rebase --abort 2>/dev/null || true

    CONFLICT_BRANCH="sync-conflict/${HOST}-$(date +%Y%m%d-%H%M%S)"
    git branch "$CONFLICT_BRANCH"
    git push -q "$REMOTE" "$CONFLICT_BRANCH"

    git fetch -q "$REMOTE" "$BRANCH"
    git reset --hard -q "$REMOTE/$BRANCH"

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
    AUXMEM_AUTOSYNC=1 git commit --no-verify -q -m "sync($HOST): conflict alert"
fi

if ! git push -q "$REMOTE" "$BRANCH" 2>/dev/null; then
    git pull --rebase --autostash -q "$REMOTE" "$BRANCH" 2>/dev/null || true
    git push -q "$REMOTE" "$BRANCH" || { log "push failed, will retry next cycle"; exit 0; }
fi

log "ok"
