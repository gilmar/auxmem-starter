"""Shared paths for Koinome corpora (governed knowledge directories)."""

from __future__ import annotations

from pathlib import Path

CONFIG = Path(".scripts/koinome.config.json")
STATE_DIR = Path(".koinome")


class CorpusPathError(Exception):
    pass


def resolve_corpus(dest):
    """Return resolved path if dest looks like a Koinome corpus."""
    dest = Path(dest).expanduser().resolve()
    if (dest / CONFIG).is_file():
        return dest
    raise CorpusPathError(f"{dest} is not a corpus (no {CONFIG})")


def managed_path(dest: Path, rel: str) -> Path:
    return Path(dest) / rel


def config_path(dest):
    """Path to the corpus config file."""
    path = Path(dest) / CONFIG
    if path.is_file():
        return path
    raise CorpusPathError(f"no corpus config under {dest}")
