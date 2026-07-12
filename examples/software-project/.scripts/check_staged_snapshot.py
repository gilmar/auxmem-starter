#!/usr/bin/env python3
"""Materialize the git index and validate the staged commit snapshot.

Exports the repository index to a temporary directory (never the working tree),
then runs full-record validation and MOC freshness checks against that snapshot.

Used by the pre-commit hook. Read-only with respect to the auxmem working tree.

Exit 0 = staged snapshot is conformant (or no auxmem paths staged).
Exit 1 = validation or MOC check failed.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AUXMEM_ROOT = SCRIPT_DIR.parent

_STAGED_PATHS = ("*.md", "72-tasks/todo.txt", "72-tasks/done.txt")


def _run(cmd: list[str], *, cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def staged_auxmem_changes(root: Path) -> bool:
    """Return True when the index includes auxmem note or task changes."""
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMRD",
            "-z",
            "--",
            *_STAGED_PATHS,
        ],
        cwd=root,
        capture_output=True,
    )
    return bool(proc.stdout.strip(b"\0"))


def materialize_index(root: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    prefix = str(dest)
    if not prefix.endswith("/"):
        prefix += "/"
    rc, out, err = _run(["git", "checkout-index", "-a", "-f", f"--prefix={prefix}"], cwd=root)
    if rc != 0:
        detail = (err or out or "").strip() or "git checkout-index failed"
        raise RuntimeError(detail)


def check_snapshot(root: Path) -> tuple[int, str]:
    """Validate the current git index as a commit snapshot. Returns (rc, message)."""
    if not (root / ".git").exists():
        return 1, "check_staged_snapshot: not a git repository"

    if not staged_auxmem_changes(root):
        return 0, ""

    tmp = Path(tempfile.mkdtemp(prefix="auxmem-staged-"))
    try:
        materialize_index(root, tmp)

        val_rc, val_out, val_err = _run(
            [sys.executable, ".scripts/validate_auxmem.py", "--all"],
            cwd=tmp,
        )
        if val_rc != 0:
            return 1, (val_out or val_err).strip() or "validation failed"

        moc_rc, moc_out, moc_err = _run(
            [sys.executable, ".scripts/gen_mocs.py", "--check"],
            cwd=tmp,
        )
        if moc_rc != 0:
            return 1, (moc_out or moc_err).strip() or "MOC freshness check failed"

        return 0, ""
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    _ = argv
    rc, message = check_snapshot(AUXMEM_ROOT)
    if message:
        print(message)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
