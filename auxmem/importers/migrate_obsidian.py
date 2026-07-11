#!/usr/bin/env python3
"""migrate_obsidian.py: import an Obsidian vault into an open-standard auxmem.

Two-pass migration:
  pass 1: plan destination path for every file (folder map + slugified names),
          build the link-resolution index against NEW locations
  pass 2: transform each note (frontmatter retrofit, wikilinks -> relative
          markdown links, strip Dataview/Templater, convert callouts) and write

Usage:
  migrate_obsidian.py --src ~/old-vault --dst ~/auxmem [--map map.json] [--dry-run]

map.json (all keys optional):
  {
    "folders": {"Projects/DataHub": "10-data-hub", "Meetings": "70-meetings"},
    "exclude": ["Templates", "Daily"],
    "default_domain": "governance"
  }
Unmapped folders land under 00-inbox/import/<original-path>/ for manual triage.
Requires: PyYAML.
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# ---------------------------------------------------------------- config ----

ASSET_EXT = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".pdf", ".csv", ".webp"}
MANUAL_EXT = {".canvas", ".base", ".excalidraw"}
SKIP_DIRS = {".obsidian", ".git", ".trash", ".scripts"}
ASSET_DIR = "95-assets"
INBOX_IMPORT = "00-inbox/import"
MANUAL_DIR = "00-inbox/import-manual"

# Domain vocabulary is loaded from the target auxmem's config at runtime
# (see load_auxmem_domains). These are fallbacks only if no config is passed.
DOMAIN_BY_PREFIX = {}
REPORT_DOMAIN = "reference"


def load_auxmem_domains(auxmem_config_path):
    """Read the target auxmem's config: build prefix->slug map and a report domain."""
    global DOMAIN_BY_PREFIX, REPORT_DOMAIN, VALID_DOMAIN
    cfg = json.loads(Path(auxmem_config_path).read_text(encoding="utf-8"))
    domains = cfg["domains"]                       # folder -> slug
    DOMAIN_BY_PREFIX = {folder[:2]: slug for folder, slug in domains.items()}
    VALID_DOMAIN = set(domains.values())
    REPORT_DOMAIN = next(iter(domains.values()))   # first domain, guaranteed valid
TYPE_BY_PREFIX = {
    "60": "adr", "70": "meeting", "80": "moc",
}
VALID_TYPES = {
    "project-doc", "governance-finding", "quality-log", "adr", "meeting",
    "1on1", "stakeholder", "exec-doc", "moc", "reference", "log",
}
VALID_STATUS = {"active", "in-review", "done", "superseded", "archived"}
VALID_DOMAIN = {"data-hub", "governance", "team", "stakeholders", "exec"}

WIKILINK = re.compile(r"(!?)\[\[([^\]|#]+)(#[^\]|]*)?(\|([^\]]*))?\]\]")
DATAVIEW_BLOCK = re.compile(r"^```\s*dataview(js)?\b.*?^```\s*$\n?", re.M | re.S)
TEMPLATER = re.compile(r"<%[\s\S]*?%>")
CALLOUT = re.compile(r"^(>\s*)\[!(\w+)\][+-]?\s*", re.M)
FM_SPLIT = re.compile(r"^---\s*$", re.M)

# ----------------------------------------------------------------- helpers --


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9.]+", "-", name.lower()).strip("-")
    return re.sub(r"-+", "-", s) or "untitled"


def file_date(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")


def load_map(path):
    if not path:
        return {}, set(), "governance"
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    folders = {k.strip("/"): v.strip("/") for k, v in cfg.get("folders", {}).items()}
    exclude = {e.strip("/") for e in cfg.get("exclude", [])}
    return folders, exclude, cfg.get("default_domain", "governance")


def map_folder(rel_parent: str, folders: dict) -> str:
    """Longest-prefix folder mapping; unmapped -> inbox import area."""
    best, best_len = None, -1
    for old, new in folders.items():
        if (rel_parent == old or rel_parent.startswith(old + "/")) and len(old) > best_len:
            remainder = rel_parent[len(old):].strip("/")
            best = f"{new}/{remainder}".strip("/")
            best_len = len(old)
    if best is not None:
        return best
    return f"{INBOX_IMPORT}/{rel_parent}".strip("/")


# ------------------------------------------------------------------ pass 1 --


def plan(src: Path, folders: dict, exclude: set):
    moves = {}          # src Path -> dst relative Path
    stem_index = {}     # lowercase old stem -> list of dst relative Paths
    report = {"manual": [], "assets": 0, "notes": 0}
    taken = set()

    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if any(str(rel).startswith(e + "/") or str(rel.parent) == e for e in exclude):
            continue

        if p.suffix.lower() == ".md":
            new_dir = map_folder(str(rel.parent).replace("\\", "/").strip("."), folders)
            new_name = slugify(p.stem) + ".md"
            report["notes"] += 1
        elif p.suffix.lower() in ASSET_EXT:
            new_dir, new_name = ASSET_DIR, slugify(p.stem) + p.suffix.lower()
            report["assets"] += 1
        elif p.suffix.lower() in MANUAL_EXT:
            new_dir, new_name = MANUAL_DIR, p.name
            report["manual"].append(str(rel))
        else:
            new_dir, new_name = MANUAL_DIR, p.name
            report["manual"].append(str(rel))

        dst_rel = Path(new_dir) / new_name
        n = 2
        while dst_rel in taken:
            dst_rel = Path(new_dir) / f"{Path(new_name).stem}-{n}{Path(new_name).suffix}"
            n += 1
        taken.add(dst_rel)
        moves[p] = dst_rel
        stem_index.setdefault(p.stem.lower(), []).append(dst_rel)
        if p.suffix.lower() != ".md":  # assets are referenced with extension
            stem_index.setdefault(p.name.lower(), []).append(dst_rel)
        # also index by full old relative path without extension ([[folder/note]])
        stem_index.setdefault(str(rel.with_suffix("")).replace("\\", "/").lower(), []).append(dst_rel)
    return moves, stem_index, report


# ------------------------------------------------------------------ pass 2 --


def retrofit_frontmatter(fm: dict, note_src: Path, dst_rel: Path, default_domain: str, warnings: list):
    prefix = dst_rel.parts[0][:2]
    fm.setdefault("title", note_src.stem)
    if not fm.get("summary"):
        fm["summary"] = (
            f"Imported from Obsidian vault ({note_src.name}). "
            "Placeholder summary, needs review."
        )
        warnings.append("summary placeholder")
    if fm.get("type") not in VALID_TYPES:
        fm["type"] = TYPE_BY_PREFIX.get(prefix, "reference")
    if fm.get("status") not in VALID_STATUS:
        fm["status"] = "in-review"
    if fm.get("domain") not in VALID_DOMAIN:
        fm["domain"] = DOMAIN_BY_PREFIX.get(prefix, default_domain)
    for field in ("created", "updated"):
        val = fm.get(field)
        if not (hasattr(val, "year") or (isinstance(val, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", val))):
            fm[field] = file_date(note_src)
    if "tag" in fm:  # singular -> plural list
        t = fm.pop("tag")
        fm.setdefault("tags", t if isinstance(t, list) else [t])
    if "tags" in fm and isinstance(fm["tags"], str):
        fm["tags"] = [x.strip() for x in fm["tags"].split(",")]
    return fm


def transform_body(text: str, dst_rel: Path, stem_index: dict, report: dict) -> str:
    n = len(DATAVIEW_BLOCK.findall(text))
    if n:
        report["dataview_stripped"] += n
        text = DATAVIEW_BLOCK.sub("<!-- removed on import: dataview block -->\n", text)
    n = len(TEMPLATER.findall(text))
    if n:
        report["templater_stripped"] += n
        text = TEMPLATER.sub("", text)
    text = CALLOUT.sub(lambda m: f"{m.group(1)}**{m.group(2).capitalize()}:** ", text)

    def replace_link(m):
        embed, target, _heading, _, alias = m.groups()
        key = target.strip().lower().removesuffix(".md")
        candidates = stem_index.get(key, [])
        label = (alias or target).strip()
        if len(candidates) != 1:
            kind = "ambiguous" if candidates else "unresolved"
            report[f"links_{kind}"].append(f"{dst_rel}: target '{target.strip()}'")
            return label  # degrade to plain text; never write a broken link
        rel_target = os.path.relpath(candidates[0], start=dst_rel.parent)
        href = rel_target.replace("\\", "/").replace(" ", "%20")
        report["links_rewritten"] += 1
        prefix = "!" if (embed and candidates[0].suffix != ".md") else ""
        return f"{prefix}[{label}]({href})"

    return WIKILINK.sub(replace_link, text)


def migrate(src: Path, dst: Path, map_file, dry_run: bool):
    folders, exclude, default_domain = load_map(map_file)
    moves, stem_index, plan_report = plan(src, folders, exclude)
    report = {
        **plan_report, "links_rewritten": 0, "dataview_stripped": 0,
        "templater_stripped": 0, "links_unresolved": [], "links_ambiguous": [],
        "fm_warnings": [],
    }

    for p, dst_rel in moves.items():
        out = dst / dst_rel
        if dry_run:
            print(f"{p.relative_to(src)}  ->  {dst_rel}")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix.lower() != ".md":
            shutil.copy2(p, out)
            continue

        raw = p.read_text(encoding="utf-8", errors="replace")
        fm, body = {}, raw
        if raw.startswith("---"):
            parts = FM_SPLIT.split(raw, maxsplit=2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1]) or {}
                    body = parts[2]
                except yaml.YAMLError:
                    report["fm_warnings"].append(f"{dst_rel}: unparseable frontmatter replaced")
                    fm = {}
        warnings = []
        fm = retrofit_frontmatter(fm, p, dst_rel, default_domain, warnings)
        if warnings:
            report["fm_warnings"].append(f"{dst_rel}: {', '.join(warnings)}")
        body = transform_body(body, dst_rel, stem_index, report)
        fm_text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=None).strip()
        out.write_text(f"---\n{fm_text}\n---\n{body.lstrip()}", encoding="utf-8")

    if not dry_run:
        write_report(dst, report)
    print(f"\nnotes: {report['notes']}  assets: {report['assets']}  "
          f"manual: {len(report['manual'])}  links rewritten: {report['links_rewritten']}  "
          f"unresolved: {len(report['links_unresolved'])}  "
          f"ambiguous: {len(report['links_ambiguous'])}")
    if not dry_run:
        print(f"report: {dst / '00-inbox' / 'migration-report.md'}")
        print("next: python3 .scripts/validate_auxmem.py --all")


def write_report(dst: Path, r: dict):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "---",
        "title: Obsidian vault migration report",
        f"summary: Automated import of the legacy Obsidian vault. {r['notes']} notes, "
        f"{r['links_rewritten']} links rewritten, {len(r['links_unresolved'])} unresolved, "
        f"{len(r['links_ambiguous'])} ambiguous, {len(r['manual'])} files for manual handling.",
        "type: log", "status: active", f"domain: {REPORT_DOMAIN}",
        f"created: {today}", f"updated: {today}", "---", "",
        f"Dataview blocks stripped: {r['dataview_stripped']}. "
        f"Templater tags stripped: {r['templater_stripped']}.", "",
    ]
    for key, title in (("links_unresolved", "Unresolved links (now plain text)"),
                       ("links_ambiguous", "Ambiguous links (now plain text)"),
                       ("manual", "Files needing manual handling (00-inbox/import-manual/)"),
                       ("fm_warnings", "Frontmatter retrofits to review")):
        if r[key]:
            lines.append(f"## {title}")
            lines.append("")
            lines.extend(f"- {item}" for item in r[key])
            lines.append("")
    out = dst / "00-inbox" / "migration-report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--map", dest="map_file")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--auxmem-config", help="target auxmem .scripts/auxmem.config.json; sets valid domains")
    args = ap.parse_args()
    if args.auxmem_config:
        load_auxmem_domains(args.auxmem_config)
    src, dst = Path(args.src).expanduser(), Path(args.dst).expanduser()
    if not src.is_dir():
        sys.exit(f"source Obsidian vault not found: {src}")
    migrate(src, dst, args.map_file, args.dry_run)


if __name__ == "__main__":
    main()
