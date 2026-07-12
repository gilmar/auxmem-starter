#!/usr/bin/env python3
"""synthesis_status.py: report the state of the synthesis layer. Deterministic;
no LLM. Run before a synthesis session to see the queue, and after to verify.

Reports three things:
  queue    source notes not yet cited by any synthesized page
  stale    synthesized pages whose sources have a newer `updated` than the
           page's `generated_at` (drift made visible)
  review   synthesized pages with review: needed

Usage: synthesis_status.py [--json]
Requires: PyYAML.
"""

import json
import sys
from datetime import date
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
AUXMEM_ROOT = SCRIPT_DIR.parent
CONFIG = json.loads((SCRIPT_DIR / "auxmem.config.json").read_text(encoding="utf-8"))
SKIP = set(CONFIG.get("skip_dirs", []))


def read_fm(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    try:
        fm = yaml.safe_load(text[3:end])
        return fm if isinstance(fm, dict) else None
    except yaml.YAMLError:
        return None


def as_date(v):
    if isinstance(v, date):
        return v.isoformat()
    return str(v) if v else ""


def scan():
    sources, syntheses = {}, []
    for p in sorted(AUXMEM_ROOT.rglob("*.md")):
        rel = str(p.relative_to(AUXMEM_ROOT)).replace("\\", "/")
        if rel.split("/")[0] in SKIP:
            continue
        fm = read_fm(p)
        if not fm:
            continue
        if fm.get("type") == "source":
            sources[rel] = as_date(fm.get("updated"))
        elif fm.get("synthesis") == "generated":
            syntheses.append({
                "path": rel,
                "generated_at": as_date(fm.get("generated_at")),
                "review": fm.get("review"),
                "sources": [s for s in (fm.get("sources") or []) if isinstance(s, str)],
                "source_updates": {},
            })
    # attach current source update dates to each synthesis
    all_updates = dict(sources)
    for p in sorted(AUXMEM_ROOT.rglob("*.md")):
        rel = str(p.relative_to(AUXMEM_ROOT)).replace("\\", "/")
        if rel.split("/")[0] in SKIP or rel in all_updates:
            continue
        fm = read_fm(p)
        if fm and fm.get("updated"):
            all_updates[rel] = as_date(fm.get("updated"))
    for s in syntheses:
        s["source_updates"] = {src: all_updates.get(src, "") for src in s["sources"]}
    return sources, syntheses


def report():
    sources, syntheses = scan()
    cited = {src for s in syntheses for src in s["sources"]}
    queue = sorted(set(sources) - cited)

    stale = []
    for s in syntheses:
        newer = [src for src, upd in s["source_updates"].items()
                 if upd and s["generated_at"] and upd > s["generated_at"]]
        if newer:
            stale.append((s["path"], newer))

    needs_review = sorted(s["path"] for s in syntheses if s["review"] != "approved")
    return {
        "sources": len(sources), "syntheses": len(syntheses),
        "queue": queue, "stale": stale, "review": needs_review,
    }


def main(argv):
    r = report()
    if "--json" in argv:
        print(json.dumps(r, indent=2))
        return 0
    print(f"sources: {r['sources']}   synthesized pages: {r['syntheses']}")
    print(f"\nunsynthesized sources ({len(r['queue'])}):")
    for q in r["queue"]:
        print(f"  {q}")
    print(f"\nstale syntheses ({len(r['stale'])}):")
    for path, newer in r["stale"]:
        print(f"  {path}  <- newer: {', '.join(newer)}")
    print(f"\nawaiting review ({len(r['review'])}):")
    for p in r["review"]:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
