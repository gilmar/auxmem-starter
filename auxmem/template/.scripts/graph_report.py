#!/usr/bin/env python3
"""graph_report.py: a deterministic view of the auxmem's link graph and its gaps.

No LLM, no database. The graph is computed on demand from what already exists in
the files: `sources:` frontmatter (typed 'cites' edges from synthesized pages)
and relative markdown links between notes ('links' edges). This is the file-only
analog of a knowledge graph: the edges are implicit in the notes, so we derive
them rather than store them.

Sections:
  edges       typed adjacency (cites, links) as an edge list
  hubs        most-referenced notes (high inbound degree)
  orphans     authored notes with no inbound and no outbound links (islands)
  co-citation source pairs drawn on together by 2+ synthesized pages
  gaps        structural holes: tags used a lot with no page, uncited sources

Targeted mode:
  --note PATH   show one note's backlinks, outbound links, and co-cited neighbors

Usage:
  graph_report.py [--json] [--note PATH] [--tag-threshold N]
Requires: PyYAML.
"""

import json
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
AUXMEM_ROOT = SCRIPT_DIR.parent
CONFIG = json.loads((SCRIPT_DIR / "auxmem.config.json").read_text(encoding="utf-8"))
# 80-moc is generated navigation; excluding it keeps MOCs from dominating as hubs.
SKIP = set(CONFIG.get("skip_dirs", [])) | {"80-moc"}

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
EXTERNAL = ("http://", "https://", "mailto:", "ftp://", "//")
# root-level agent/readme files are orientation, not knowledge nodes
META_FILES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md"}


def rel(p: Path) -> str:
    return str(p.relative_to(AUXMEM_ROOT)).replace("\\", "/")


def in_scope(relpath: str) -> bool:
    if relpath.split("/")[0] in SKIP:
        return False
    if "/" not in relpath and relpath in META_FILES:
        return False
    return True


def split_fm(text):
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    try:
        fm = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        fm = None
    body = text[end + 4:]
    return (fm if isinstance(fm, dict) else None), body


def resolve_link(target: str, from_file: Path):
    """Resolve a markdown link target to an auxmem-root-relative .md path, or None."""
    t = target.strip().split()[0]  # drop any ' "title"' suffix
    if t.startswith(EXTERNAL) or t.startswith("#"):
        return None
    t = t.split("#", 1)[0]
    if not t.endswith(".md"):
        return None
    try:
        dest = (from_file.parent / t).resolve()
        dest.relative_to(AUXMEM_ROOT)
    except (ValueError, OSError):
        return None
    return rel(dest) if dest.exists() else None


def scan():
    nodes = {}          # relpath -> {type, title, tags, synthesis}
    cites = []          # (synth_page, source_path)
    links = []          # (from, to)
    for p in sorted(AUXMEM_ROOT.rglob("*.md")):
        r = rel(p)
        if not in_scope(r):
            continue
        fm, body = split_fm(p.read_text(encoding="utf-8", errors="replace"))
        fm = fm or {}
        nodes[r] = {
            "type": fm.get("type"),
            "title": fm.get("title") or r,
            "tags": [t for t in (fm.get("tags") or []) if isinstance(t, str)],
            "synthesis": fm.get("synthesis") == "generated",
        }
        for s in (fm.get("sources") or []):
            if isinstance(s, str):
                cites.append((r, s))
        for m in LINK_RE.finditer(body):
            tgt = resolve_link(m.group(1), p)
            if tgt and tgt != r:
                links.append((r, tgt))
    return nodes, cites, links


def degrees(nodes, edges):
    indeg, outdeg = defaultdict(int), defaultdict(int)
    inbound = defaultdict(set)
    for a, b in edges:
        outdeg[a] += 1
        indeg[b] += 1
        inbound[b].add(a)
    return indeg, outdeg, inbound


def build():
    nodes, cites, links = scan()
    all_edges = [(a, b) for a, b in links] + [(a, b) for a, b in cites]
    indeg, outdeg, inbound = degrees(nodes, all_edges)

    hubs = sorted(
        ((r, indeg[r]) for r in nodes if indeg[r] > 0),
        key=lambda x: (-x[1], x[0]),
    )

    orphans = sorted(
        r for r, n in nodes.items()
        if indeg[r] == 0 and outdeg[r] == 0
        and n["type"] not in ("source", "moc")
        and not n["synthesis"]
    )

    # co-citation: sources appearing together in the same synthesized page
    cocite = defaultdict(int)
    by_page = defaultdict(list)
    for page, src in cites:
        by_page[page].append(src)
    for srcs in by_page.values():
        for a, b in combinations(sorted(set(srcs)), 2):
            cocite[(a, b)] += 1
    cocited = sorted(
        ((pair, c) for pair, c in cocite.items() if c >= 2),
        key=lambda x: (-x[1], x[0]),
    )

    return nodes, cites, links, all_edges, hubs, orphans, inbound, cocited


def gaps(nodes, cites, tag_threshold):
    # tags used often with no page whose slug/title matches the tag
    tag_counts = defaultdict(int)
    for n in nodes.values():
        for t in n["tags"]:
            tag_counts[t] += 1
    slugs = set()
    for r, n in nodes.items():
        slugs.add(Path(r).stem.lower())
        slugs.add(str(n["title"]).lower().strip())
    tag_gaps = sorted(
        (t, c) for t, c in tag_counts.items()
        if c >= tag_threshold and t.lower() not in slugs
    )
    tag_gaps.sort(key=lambda x: (-x[1], x[0]))

    # sources cited by nothing (also reported by synthesis_status; noted here for graph completeness)
    cited = {s for _, s in cites}
    uncited_sources = sorted(
        r for r, n in nodes.items() if n["type"] == "source" and r not in cited
    )
    return tag_gaps, uncited_sources


def targeted(note, nodes, all_edges, cites):
    if note not in nodes:
        print(f"note not found in graph: {note}", file=sys.stderr)
        return 1
    outbound = sorted({b for a, b in all_edges if a == note})
    backlinks = sorted({a for a, b in all_edges if b == note})
    # co-cited neighbors: sources sharing a synthesized page with this note (if note is a source)
    neighbors = set()
    by_page = defaultdict(set)
    for page, src in cites:
        by_page[page].add(src)
    for srcs in by_page.values():
        if note in srcs:
            neighbors |= (srcs - {note})
    print(f"# {note}")
    print(f"  title: {nodes[note]['title']}")
    print(f"\nbacklinks ({len(backlinks)}):")
    for b in backlinks:
        print(f"  <- {b}")
    print(f"\noutbound ({len(outbound)}):")
    for o in outbound:
        print(f"  -> {o}")
    if neighbors:
        print(f"\nco-cited with ({len(neighbors)}):")
        for n in sorted(neighbors):
            print(f"  ~ {n}")
    return 0


def main(argv):
    tag_threshold = 3
    if "--tag-threshold" in argv:
        tag_threshold = int(argv[argv.index("--tag-threshold") + 1])
    nodes, cites, links, all_edges, hubs, orphans, inbound, cocited = build()

    if "--note" in argv:
        return targeted(argv[argv.index("--note") + 1], nodes, all_edges, cites)

    tag_gaps, uncited_sources = gaps(nodes, cites, tag_threshold)

    if "--json" in argv:
        print(json.dumps({
            "nodes": len(nodes),
            "edges": {"cites": len(cites), "links": len(links)},
            "hubs": hubs[:20],
            "orphans": orphans,
            "co_citation": [{"pair": list(p), "count": c} for p, c in cocited],
            "gaps": {"tags_without_page": tag_gaps, "uncited_sources": uncited_sources},
        }, indent=2))
        return 0

    print(f"nodes: {len(nodes)}   edges: {len(cites)} cites, {len(links)} links\n")
    print("hubs (most referenced):")
    for r, d in hubs[:10]:
        print(f"  {d:3}  {r}")
    if not hubs:
        print("  none yet")

    print(f"\norphans (no links in or out) ({len(orphans)}):")
    for o in orphans:
        print(f"  {o}")
    if not orphans:
        print("  none")

    print(f"\nco-citation (sources drawn on together by 2+ syntheses) ({len(cocited)}):")
    for (a, b), c in cocited[:15]:
        print(f"  {c}x  {a}  +  {b}")
    if not cocited:
        print("  none")

    print("\ngaps:")
    print(f"  tags used >= {tag_threshold}x with no page ({len(tag_gaps)}):")
    for t, c in tag_gaps:
        print(f"    {c}x  {t}")
    if not tag_gaps:
        print("    none")
    print(f"  sources cited by nothing ({len(uncited_sources)}):")
    for s in uncited_sources:
        print(f"    {s}")
    if not uncited_sources:
        print("    none")
    print("\nNote: this is structural, not semantic. It finds islands, hubs, and")
    print("holes in the graph. It cannot judge whether two notes contradict; that")
    print("needs a reading pass. See docs/SYNTHESIS.md for the review loop.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except Exception:
            pass
        sys.exit(0)
