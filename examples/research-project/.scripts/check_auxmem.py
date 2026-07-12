#!/usr/bin/env python3
"""Read-only auxmem conformance check for humans and CI.

Runs, in order:
  1. validate_auxmem.py --all
  2. gen_mocs.py --check
  3. optional manifest tooling presence (--manifest)
  4. optional git cleanliness (--git)

Never modifies files. Exit 0 = conformant. Exit 1 = failed check.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AUXMEM_ROOT = SCRIPT_DIR.parent

_MANIFEST_TOOLING = (
    ".scripts/validate_auxmem.py",
    ".scripts/gen_mocs.py",
    ".scripts/auxmem.config.json",
    ".scripts/check_auxmem.py",
)


def _run(cmd: list[str], *, cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _fail(phase: str, out: str, err: str) -> tuple[int, str]:
    detail = (out or err or "").strip()
    if detail:
        return 1, f"{phase} failed:\n{detail}"
    return 1, f"{phase} failed (non-zero exit; no output captured)"


def check_validation(root: Path) -> tuple[int, str]:
    rc, out, err = _run([sys.executable, ".scripts/validate_auxmem.py", "--all"], cwd=root)
    if rc != 0:
        return _fail("Validation", out, err)
    return 0, (out or err or "validation clean.").strip()


def check_moc_freshness(root: Path) -> tuple[int, str]:
    rc, out, err = _run([sys.executable, ".scripts/gen_mocs.py", "--check"], cwd=root)
    if rc != 0:
        return _fail("MOC freshness", out, err)
    detail = (out or err or "MOCs up to date.").strip()
    return 0, detail


def check_manifest(root: Path) -> tuple[int, str]:
    manifest_path = root / ".auxmem" / "manifest.json"
    if not manifest_path.is_file():
        return 0, "manifest check skipped (no .auxmem/manifest.json)"

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return 1, f"manifest check failed: invalid JSON in .auxmem/manifest.json ({exc})"

    files = manifest.get("files", {})
    missing = [rel for rel in _MANIFEST_TOOLING if rel in files and not (root / rel).is_file()]
    if missing:
        return 1, "manifest check failed: missing managed tooling:\n" + "\n".join(f"  - {m}" for m in missing)

    mismatched = []
    for rel, meta in files.items():
        if rel not in _MANIFEST_TOOLING:
            continue
        path = root / rel
        if not path.is_file():
            continue
        expected = meta.get("sha256")
        if not expected:
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            mismatched.append(rel)
    if mismatched:
        return 1, "manifest check failed: hash mismatch for:\n" + "\n".join(
            f"  - {m}" for m in mismatched
        )

    return 0, "manifest tooling integrity ok"


def check_git_clean(root: Path) -> tuple[int, str]:
    if not (root / ".git").is_dir():
        return 1, "git check failed: not a git repository"
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip() or "git status failed"
        return 1, f"git check failed: {detail}"
    if proc.stdout.strip():
        return 1, "git check failed: uncommitted changes\n" + proc.stdout.strip()
    return 0, "git working tree clean"


def run_checks(
    root: Path,
    *,
    manifest: bool = False,
    git: bool = False,
) -> tuple[int, list[str]]:
    """Run conformance checks. Returns (exit_code, human-readable report lines)."""
    lines: list[str] = []

    rc, msg = check_validation(root)
    lines.append(msg)
    if rc != 0:
        return rc, lines

    rc, msg = check_moc_freshness(root)
    lines.append(msg)
    if rc != 0:
        return rc, lines

    if manifest:
        rc, msg = check_manifest(root)
        lines.append(msg)
        if rc != 0:
            return rc, lines

    if git:
        rc, msg = check_git_clean(root)
        lines.append(msg)
        if rc != 0:
            return rc, lines

    lines.append("auxmem conformance check passed.")
    return 0, lines


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    manifest = "--manifest" in args
    git = "--git" in args
    rc, lines = run_checks(AUXMEM_ROOT, manifest=manifest, git=git)
    print("\n".join(lines))
    return rc


if __name__ == "__main__":
    sys.exit(main())
