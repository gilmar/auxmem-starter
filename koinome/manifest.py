"""Template manifest policy and bundled-template verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ALLOWED_POLICIES = frozenset({"overwrite", "merge", "merge3"})


def policy_for(rel: str) -> str | None:
    if rel == ".scripts/koinome.config.json":
        return "merge"
    if rel == ".gitattributes":
        return "merge3"
    if rel.startswith(".github/workflows/") and rel.endswith((".yml", ".yaml")):
        return "overwrite"
    if rel.startswith(".schemas/"):
        return "overwrite"
    if rel.startswith(".scripts/") or rel == "bootstrap.sh":
        return "overwrite"
    if rel.startswith(".skills/"):
        return "merge3"
    if rel in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md"):
        return "merge3"
    if rel.startswith("docs/") and rel.endswith(".md"):
        return "merge3"
    if rel.startswith("90-templates/") and rel.endswith(".md"):
        return "merge3"
    return None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def managed_files_in_template(template_dir: Path) -> dict[str, str]:
    """Return rel -> policy for every managed file under template_dir."""
    out: dict[str, str] = {}
    for path in sorted(template_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(template_dir)).replace("\\", "/")
        if "__pycache__" in rel.split("/") or rel.endswith(".pyc"):
            continue
        pol = policy_for(rel)
        if pol:
            out[rel] = pol
    return out


def verify_bundled_template(template_dir: Path, manifest_path: Path) -> None:
    """Raise ValueError if the bundled template manifest or files are corrupt."""
    if not manifest_path.is_file():
        raise ValueError(f"template manifest missing: {manifest_path}")
    if not template_dir.is_dir():
        raise ValueError(f"template directory missing: {template_dir}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"template manifest is not valid JSON: {exc}") from exc

    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("template manifest missing 'files' mapping")

    errors: list[str] = []
    expected = managed_files_in_template(template_dir)

    for rel, pol in expected.items():
        if rel not in files:
            errors.append(f"managed file missing from manifest: {rel}")

    for rel, meta in files.items():
        if not isinstance(meta, dict):
            errors.append(f"manifest entry for {rel} is not an object")
            continue
        policy = meta.get("policy")
        if policy not in ALLOWED_POLICIES:
            errors.append(f"unsupported policy for {rel}: {policy!r}")
        template_file = template_dir / rel
        if not template_file.is_file():
            errors.append(f"template file missing on disk: {rel}")
            continue
        expected_hash = meta.get("sha256")
        if not expected_hash:
            errors.append(f"manifest entry for {rel} missing sha256")
            continue
        actual = sha256_file(template_file)
        if actual != expected_hash:
            errors.append(f"hash mismatch for {rel}")

    if errors:
        raise ValueError("bundled template verification failed:\n" + "\n".join(f"  - {e}" for e in errors))
