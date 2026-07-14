"""Normalize line endings for scripts that bash must execute."""

from __future__ import annotations

from pathlib import Path


def ensure_lf_bytes(data: bytes) -> bytes:
    """Convert CRLF/CR to LF without rewriting already-LF content."""
    if b"\r" not in data:
        return data
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def is_bash_script(path: Path) -> bool:
    name = path.name
    return name.endswith(".sh") or name == "bootstrap.sh" or name == "pre-commit"


def normalize_script_file(path: Path) -> bool:
    """Rewrite *path* with LF endings if needed. Returns True when bytes changed."""
    if not path.is_file() or not is_bash_script(path):
        return False
    raw = path.read_bytes()
    fixed = ensure_lf_bytes(raw)
    if fixed == raw:
        return False
    path.write_bytes(fixed)
    return True


def normalize_corpus_shell_scripts(corpus_root: Path) -> list[str]:
    """Ensure bootstrap and .scripts shell/hooks use LF. Returns changed rel paths."""
    root = Path(corpus_root)
    candidates = [root / "bootstrap.sh", root / ".scripts" / "pre-commit"]
    scripts_dir = root / ".scripts"
    if scripts_dir.is_dir():
        candidates.extend(sorted(scripts_dir.glob("*.sh")))
    changed: list[str] = []
    for path in candidates:
        if normalize_script_file(path):
            changed.append(str(path.relative_to(root)).replace("\\", "/"))
    return changed
