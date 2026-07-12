#!/usr/bin/env python3
"""build_manifest.py: (maintainer tool) generate koinome/template/.koinome-manifest.json.

Run after changing the template and bumping koinome/version.py. The manifest
lists every MANAGED file (tooling, config, guidance) with its upgrade policy
and a content hash. Files not listed are user content and are never touched by
`koinome upgrade`.

Policies:
  overwrite  tooling; replaced on upgrade (backed up; warned if user-edited)
  merge      structured JSON merge preserving user values (koinome.config.json)
  merge3     git 3-way merge against the corpus's snapshot (guidance, docs, templates)
"""

import json
import sys
from pathlib import Path

STARTER_ROOT = Path(__file__).resolve().parent
TEMPLATE = STARTER_ROOT / "koinome" / "template"
sys.path.insert(0, str(STARTER_ROOT))
from koinome.manifest import policy_for, sha256_file
from koinome.version import CONFORMANCE_VERSION, TEMPLATE_VERSION


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
            files[rel] = {"policy": pol, "sha256": sha256_file(p)}
    manifest = {
        "template_version": TEMPLATE_VERSION,
        "conformance_version": CONFORMANCE_VERSION,
        "files": files,
    }
    out = TEMPLATE / ".koinome-manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {out} ({len(files)} managed files, "
        f"template {TEMPLATE_VERSION}, conformance {CONFORMANCE_VERSION})"
    )


if __name__ == "__main__":
    build()
