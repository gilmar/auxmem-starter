#!/usr/bin/env python3
"""Validated git sync with quarantine for an auxmem folder.

State machine:
  1. Resolve auxmem root, branch, and remote (env overrides supported).
  2. Acquire a per-repository lock under .git/auxmem-sync.lock/.
  3. Stage pending changes; validate the index snapshot before any canonical commit.
  4. On valid pending auxmem changes: verified commit, pull --rebase, conformance check, push.
  5. On invalid pending auxmem changes: quarantine branch, restore canonical tip, write alert.
  6. On rebase conflict: preserve local state on a conflict branch, reset to remote, alert.

Exit codes:
  0  success
  1  operation failure (lock held, missing remote when required, push failure, etc.)
  3  quarantine or conflict branch created (invalid snapshot or rebase conflict)
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OK = 0
FAIL = 1
QUARANTINE = 3

_PYTHON = sys.executable


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _log(msg: str) -> None:
    print(f"[auxmem-sync {_iso_now()}] {msg}")


def _short_host() -> str:
    host = socket.gethostname().split(".")[0]
    return re.sub(r"[^a-zA-Z0-9-]+", "-", host).strip("-") or "host"


def _run(cmd: list[str], *, cwd: Path, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return _run(["git", *args], cwd=cwd)


def _git_out(cwd: Path, *args: str, default: str = "") -> str:
    proc = _git(cwd, *args)
    if proc.returncode != 0:
        return default
    return proc.stdout.strip()


def _read_config(root: Path) -> dict:
    return json.loads((root / ".scripts" / "auxmem.config.json").read_text(encoding="utf-8"))


def _first_domain(config: dict) -> str | None:
    domains = config.get("domains") or {}
    if not domains:
        return None
    return next(iter(domains.values()))


def resolve_sync_target(auxmem_arg: str | None) -> Path:
    if auxmem_arg:
        raw = auxmem_arg
    elif os.environ.get("AUXMEM"):
        raw = os.environ["AUXMEM"]
    else:
        raw = str(Path.cwd())
    root = Path(raw).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"auxmem folder not found: {root}")
    if not (root / ".scripts" / "auxmem.config.json").is_file():
        raise FileNotFoundError(f"not an auxmem (missing .scripts/auxmem.config.json): {root}")
    return root


def resolve_remote_branch(root: Path) -> tuple[str, str]:
    branch = os.environ.get("AUXMEM_SYNC_BRANCH", "").strip()
    remote = os.environ.get("AUXMEM_SYNC_REMOTE", "").strip()
    if not branch:
        branch = _git_out(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not branch:
        raise RuntimeError("cannot determine current git branch")
    if not remote:
        remote = _git_out(root, "config", f"branch.{branch}.remote") or "origin"
    return remote, branch


def remote_available(root: Path, remote: str) -> bool:
    return _git(root, "remote", "get-url", remote).returncode == 0


def acquire_lock(root: Path) -> Path | None:
    lock = root / ".git" / "auxmem-sync.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        return None
    return lock


def release_lock(lock: Path | None) -> None:
    if lock is None:
        return
    try:
        lock.rmdir()
    except OSError:
        pass


def worktree_dirty(root: Path) -> bool:
    return bool(_git_out(root, "status", "--porcelain"))


def staged_auxmem_changes(root: Path) -> bool:
    proc = _git(
        root,
        "diff",
        "--cached",
        "--name-only",
        "--diff-filter=ACMRD",
        "-z",
        "--",
        "*.md",
        "72-tasks/todo.txt",
        "72-tasks/done.txt",
    )
    return bool(proc.stdout.strip("\0"))


def check_staged_snapshot(root: Path) -> tuple[int, str]:
    proc = _run([_PYTHON, ".scripts/check_staged_snapshot.py"], cwd=root)
    message = (proc.stdout or proc.stderr).strip()
    return proc.returncode, message


def check_conformance(root: Path) -> tuple[int, str]:
    proc = _run([_PYTHON, ".scripts/check_auxmem.py"], cwd=root)
    message = (proc.stdout or proc.stderr).strip()
    return proc.returncode, message


def _write_inbox_alert(
    root: Path,
    *,
    filename: str,
    title: str,
    summary: str,
    body: str,
    domain: str,
) -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = root / "00-inbox" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"title: {title}",
                f"summary: {summary}",
                "type: log",
                "status: active",
                f"domain: {domain}",
                f"created: {today}",
                f"updated: {today}",
                "---",
                "",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_auxmem_alert(root: Path, *, filename: str, body: str) -> Path:
    path = root / ".auxmem" / "alerts" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.rstrip() + "\n", encoding="utf-8")
    return path


def write_invalid_alert(root: Path, branch: str, detail: str, domain: str | None) -> Path:
    ts = _timestamp()
    body = (
        f"Automatic sync rejected invalid pending changes.\n\n"
        f"Quarantine branch: `{branch}`\n\n"
        f"Recovery:\n"
        f"  git fetch origin {branch}\n"
        f"  git checkout {branch}\n"
        f"  # fix validation issues, then merge or cherry-pick onto your canonical branch\n\n"
        f"Validation output:\n{detail}\n"
    )
    if domain:
        return _write_inbox_alert(
            root,
            filename=f"sync-invalid-{ts}.md",
            title=f"Sync invalid on {_short_host()}",
            summary=(
                f"Automatic sync quarantined invalid pending changes on branch {branch}. "
                "Canonical branch was restored."
            ),
            body=body,
            domain=domain,
        )
    return _write_auxmem_alert(root, filename=f"sync-invalid-{ts}.md", body=body)


def write_conflict_alert(root: Path, branch: str, domain: str | None) -> Path:
    ts = _timestamp()
    body = (
        f"Automatic sync hit a rebase conflict.\n\n"
        f"Conflict branch: `{branch}`\n\n"
        f"Recovery:\n"
        f"  git merge {branch}\n"
        f"  # resolve, validate, then delete the branch:\n"
        f"  git branch -d {branch}\n"
        f"  git push origin --delete {branch}\n"
    )
    if domain:
        return _write_inbox_alert(
            root,
            filename=f"sync-conflict-{ts}.md",
            title=f"Sync conflict on {_short_host()}",
            summary=(
                f"Automatic sync preserved local commits on {branch} and reset "
                "the canonical branch to the remote."
            ),
            body=body,
            domain=domain,
        )
    return _write_auxmem_alert(root, filename=f"sync-conflict-{ts}.md", body=body)


def quarantine_invalid_state(
    root: Path,
    *,
    remote: str,
    canonical_tip: str,
    detail: str,
    domain: str | None,
) -> int:
    host = _short_host()
    branch = f"sync-invalid/{host}/{_timestamp()}"
    msg = f"sync({host}): quarantine invalid state {_iso_now()}"

    if _git(root, "commit", "--no-verify", "-m", msg).returncode != 0:
        _log("failed to create quarantine commit")
        _git(root, "reset", "--mixed", canonical_tip)
        return FAIL

    if _git(root, "branch", branch).returncode != 0:
        _log(f"failed to create quarantine branch {branch}")
        _git(root, "reset", "--hard", canonical_tip)
        return FAIL

    if remote_available(root, remote):
        push = _git(root, "push", remote, branch)
        if push.returncode != 0:
            _log(f"failed to push quarantine branch {branch}")
            _git(root, "checkout", "-")
            _git(root, "reset", "--hard", canonical_tip)
            return FAIL

    _git(root, "reset", "--hard", canonical_tip)
    alert = write_invalid_alert(root, branch, detail, domain)
    _log(f"invalid state quarantined on {branch}; alert: {alert.relative_to(root)}")
    _log(f"recovery: git fetch {remote} {branch} && git checkout {branch}")
    return QUARANTINE


def handle_rebase_conflict(
    root: Path,
    *,
    remote: str,
    branch: str,
    domain: str | None,
) -> int:
    _git(root, "rebase", "--abort")
    host = _short_host()
    conflict_branch = f"sync-conflict/{host}/{_timestamp()}"

    if _git(root, "branch", conflict_branch).returncode != 0:
        _log("failed to preserve conflict branch")
        return FAIL

    if remote_available(root, remote):
        if _git(root, "push", remote, conflict_branch).returncode != 0:
            _log(f"failed to push conflict branch {conflict_branch}")
            return FAIL
        if _git(root, "fetch", remote, branch).returncode != 0:
            _log(f"failed to fetch {remote}/{branch}")
            return FAIL
        if _git(root, "reset", "--hard", f"{remote}/{branch}").returncode != 0:
            _log("failed to reset canonical branch to remote")
            return FAIL
    else:
        _log(f"remote {remote} unavailable; conflict branch kept locally as {conflict_branch}")

    alert = write_conflict_alert(root, conflict_branch, domain)
    _log(f"rebase conflict; preserved {conflict_branch}; alert: {alert.relative_to(root)}")
    return QUARANTINE


def sync_auxmem(root: Path) -> int:
    remote, branch = resolve_remote_branch(root)
    config = _read_config(root)
    domain = _first_domain(config)
    host = _short_host()

    lock = acquire_lock(root)
    if lock is None:
        _log("another sync is running for this auxmem, skipping")
        return FAIL

    try:
        canonical_tip = _git_out(root, "rev-parse", "HEAD")
        if not canonical_tip:
            _log("not a git repository")
            return FAIL

        if worktree_dirty(root):
            _git(root, "add", "-A")

        if staged_auxmem_changes(root):
            rc, detail = check_staged_snapshot(root)
            if rc != 0:
                return quarantine_invalid_state(
                    root,
                    remote=remote,
                    canonical_tip=canonical_tip,
                    detail=detail or "staged snapshot validation failed",
                    domain=domain,
                )
            commit = _git(root, "commit", "-m", f"sync({host}): {_iso_now()}")
            if commit.returncode != 0:
                _log("verified commit failed")
                return FAIL
        elif worktree_dirty(root):
            commit = _git(root, "commit", "-m", f"sync({host}): {_iso_now()}")
            if commit.returncode != 0:
                _log("commit failed")
                return FAIL

        if remote_available(root, remote):
            pull = _git(root, "pull", "--rebase", "--autostash", remote, branch)
            if pull.returncode != 0:
                return handle_rebase_conflict(root, remote=remote, branch=branch, domain=domain)

        rc, detail = check_conformance(root)
        if rc != 0:
            _log("conformance check failed before push:")
            print(detail)
            return FAIL

        if remote_available(root, remote):
            push = _git(root, "push", remote, branch)
            if push.returncode != 0:
                _log("push failed")
                if (push.stderr or push.stdout).strip():
                    print((push.stderr or push.stdout).strip())
                return FAIL

        _log("ok")
        return OK
    finally:
        release_lock(lock)


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    try:
        root = resolve_sync_target(args[0] if args else None)
    except FileNotFoundError as exc:
        _log(str(exc))
        return FAIL
    try:
        return sync_auxmem(root)
    except RuntimeError as exc:
        _log(str(exc))
        return FAIL


if __name__ == "__main__":
    sys.exit(main())
