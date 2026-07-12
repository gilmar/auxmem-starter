#!/usr/bin/env python3
"""build_manifest.py: (maintainer tool) generate auxmem/template/.auxmem-manifest.json.

Run after changing the template and bumping auxmem/version.py. The manifest
lists every MANAGED file (tooling, config, guidance) with its upgrade policy
and a content hash. Files not listed are user content and are never touched by
`auxmem upgrade`.

Policies:
  overwrite  tooling; replaced on upgrade (backed up; warned if user-edited)
  merge      structured JSON merge preserving user values (auxmem.config.json)
  merge3     git 3-way merge against the auxmem's snapshot (guidance, docs, templates)
"""

import hashlib
import json
import sys
from pathlib import Path

STARTER_ROOT = Path(__file__).resolve().parent
TEMPLATE = STARTER_ROOT / "auxmem" / "template"
sys.path.insert(0, str(STARTER_ROOT))
from auxmem.version import TEMPLATE_VERSION


def policy_for(rel: str):
    if rel == ".scripts/auxmem.config.json":
        return "merge"
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
    return None  # user content: not managed


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    files = {}
    for p in sorted(TEMPLATE.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(TEMPLATE)).replace("\\", "/")
        if "__pycache__" in rel.split("/") or rel.endswith(".pyc"):
            continue
        pol = policy_for(rel)
        if pol:
            files[rel] = {"policy": pol, "sha256": sha256(p)}
    manifest = {"template_version": TEMPLATE_VERSION, "files": files}
    out = TEMPLATE / ".auxmem-manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(files)} managed files, version {TEMPLATE_VERSION})")


if __name__ == "__main__":
    build()
