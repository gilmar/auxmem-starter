#!/usr/bin/env python3
"""restructure_export.py: stage 2 of the Obsidian import pipeline.

Takes obsidian-export output (already CommonMark: wikilinks resolved to
relative markdown links) and restructures it into the auxmem:
  - folder mapping (longest prefix) + slugified filenames
  - exact link remapping through the move table (no heuristics: paths are
    already resolved, they just need re-pointing at new locations)
  - frontmatter retrofit to the auxmem schema
  - strips Dataview blocks (any fence length) and escaped Templater tags,
    converts escaped callouts to bold blockquotes
  - migration report as a valid auxmem note, including obsidian-export's own
    unresolved-link warnings (.export-warnings.txt)

Usage:
  restructure_export.py --src exported/ --dst ~/auxmem [--map map.json] [--dry-run]

map.json format identical to migrate_obsidian.py.
Requires: PyYAML.
"""

import argparse
import json
import os
import re
import shutil
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import yaml

# ---------------------------------------------------------------- config ----

ASSET_EXT = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".pdf", ".csv", ".webp"}
ASSET_DIR = "95-assets"
INBOX_IMPORT = "00-inbox/import"
MANUAL_DIR = "00-inbox/import-manual"

# domain vocabulary loaded from the target auxmem config at runtime
DOMAIN_BY_PREFIX = {}
REPORT_DOMAIN = "reference"


def load_auxmem_domains(auxmem_config_path):
    global DOMAIN_BY_PREFIX, REPORT_DOMAIN, VALID_DOMAIN
    cfg = json.loads(Path(auxmem_config_path).read_text(encoding="utf-8"))
    domains = cfg["domains"]
    DOMAIN_BY_PREFIX = {folder[:2]: slug for folder, slug in domains.items()}
    VALID_DOMAIN = set(domains.values())
    REPORT_DOMAIN = next(iter(domains.values()))
TYPE_BY_PREFIX = {"60": "adr", "70": "meeting", "80": "moc"}
VALID_TYPES = {
    "project-doc", "governance-finding", "quality-log", "adr", "meeting",
    "1on1", "stakeholder", "exec-doc", "moc", "reference", "log",
}
VALID_STATUS = {"active", "in-review", "done", "superseded", "archived"}
VALID_DOMAIN = set()

MD_LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)]+)\)")
DATAVIEW_BLOCK = re.compile(r"^`{3,}\s*dataview(js)?\b.*?^`{3,}\s*$\n?", re.M | re.S)
TEMPLATER = re.compile(r"\\?<%[\s\S]*?%\\?>")
CALLOUT = re.compile(r"^(\s*>\s*)\\?\[!(\w+)\\?\][+-]?\s*", re.M)
EMPTY_QUOTE_BEFORE_CALLOUT = re.compile(r"^ ?>\s*\n(?=\s*>\s*\\?\[!)", re.M)
FM_SPLIT = re.compile(r"^---\s*$", re.M)

# ----------------------------------------------------------------- helpers --


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9.]+", "-", name.lower()).strip("-")
    return re.sub(r"-+", "-", s) or "untitled"


def file_date(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")


def load_map(path):
    if not path:
        return {}, "governance"
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    folders = {k.strip("/"): v.strip("/") for k, v in cfg.get("folders", {}).items()}
    return folders, cfg.get("default_domain", "governance")


def map_folder(rel_parent: str, folders: dict) -> str:
    best, best_len = None, -1
    for old, new in folders.items():
        if (rel_parent == old or rel_parent.startswith(old + "/")) and len(old) > best_len:
            remainder = rel_parent[len(old):].strip("/")
            best = f"{new}/{remainder}".strip("/")
            best_len = len(old)
    return best if best is not None else f"{INBOX_IMPORT}/{rel_parent}".strip("/")


# ------------------------------------------------------------------ pass 1 --


def plan(src: Path, folders: dict):
    moves = {}  # old auxmem-relative posix path (str) -> new relative Path
    files = []  # (src Path, old_rel str, new_rel Path)
    taken, notes, assets, manual = set(), 0, 0, []
    for p in sorted(src.rglob("*")):
        if not p.is_file() or p.name == ".export-warnings.txt":
            continue
        old_rel = str(p.relative_to(src)).replace("\\", "/")
        parent = str(PurePosixPath(old_rel).parent)
        parent = "" if parent == "." else parent
        if p.suffix.lower() == ".md":
            new_dir, new_name = map_folder(parent, folders), slugify(p.stem) + ".md"
            notes += 1
        elif p.suffix.lower() in ASSET_EXT:
            new_dir, new_name = ASSET_DIR, slugify(p.stem) + p.suffix.lower()
            assets += 1
        else:
            new_dir, new_name = MANUAL_DIR, p.name
            manual.append(old_rel)
        new_rel = Path(new_dir) / new_name
        n = 2
        while new_rel in taken:
            new_rel = Path(new_dir) / f"{Path(new_name).stem}-{n}{Path(new_name).suffix}"
            n += 1
        taken.add(new_rel)
        moves[old_rel.lower()] = new_rel
        files.append((p, old_rel, new_rel))
    return moves, files, {"notes": notes, "assets": assets, "manual": manual}


# ------------------------------------------------------------------ pass 2 --


def retrofit_frontmatter(fm, note_src, new_rel, default_domain, warnings):
    prefix = new_rel.parts[0][:2]
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
    if "tag" in fm:
        t = fm.pop("tag")
        fm.setdefault("tags", t if isinstance(t, list) else [t])
    if isinstance(fm.get("tags"), str):
        fm["tags"] = [x.strip() for x in fm["tags"].split(",")]
    return fm


def remap_links(text, old_rel, new_rel, moves, report):
    """Exact path remapping: decode, resolve against old location, look up
    the move table, re-relativize against the new location."""
    old_dir = PurePosixPath(old_rel).parent

    def repl(m):
        bang, label, href = m.groups()
        if href.startswith(("http://", "https://", "mailto:", "#")):
            return m.group(0)
        path_part, _, frag = href.partition("#")
        decoded = urllib.parse.unquote(path_part)
        resolved = os.path.normpath(str(old_dir / decoded)).replace("\\", "/").lstrip("./")
        target = moves.get(resolved.lower())
        if target is None:
            report["links_unmapped"].append(f"{new_rel}: target '{decoded}'")
            return label  # degrade to plain text, never a broken link
        rel = os.path.relpath(target, start=new_rel.parent).replace("\\", "/")
        report["links_remapped"] += 1
        return f"{bang}[{label}]({rel.replace(' ', '%20')})"

    return MD_LINK.sub(repl, text)


def transform_body(text, old_rel, new_rel, moves, report):
    n = len(DATAVIEW_BLOCK.findall(text))
    if n:
        report["dataview_stripped"] += n
        text = DATAVIEW_BLOCK.sub("<!-- removed on import: dataview block -->\n", text)
    n = len(TEMPLATER.findall(text))
    if n:
        report["templater_stripped"] += n
        text = TEMPLATER.sub("", text)
    text = EMPTY_QUOTE_BEFORE_CALLOUT.sub("", text)
    text = CALLOUT.sub(lambda m: f"{m.group(1)}**{m.group(2).capitalize()}:** ", text)
    return remap_links(text, old_rel, new_rel, moves, report)


def run(src: Path, dst: Path, map_file, dry_run: bool):
    folders, default_domain = load_map(map_file)
    moves, files, stats = plan(src, folders)
    report = {
        **stats, "links_remapped": 0, "links_unmapped": [],
        "dataview_stripped": 0, "templater_stripped": 0, "fm_warnings": [],
        "export_warnings": [],
    }
    warn_file = src / ".export-warnings.txt"
    if warn_file.exists():
        report["export_warnings"] = [
            ln.strip() for ln in warn_file.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith(("Reference:", "Source:"))
        ]

    for p, old_rel, new_rel in files:
        if dry_run:
            print(f"{old_rel}  ->  {new_rel}")
            continue
        out = dst / new_rel
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
                    report["fm_warnings"].append(f"{new_rel}: unparseable frontmatter replaced")
                    fm = {}
        warnings = []
        fm = retrofit_frontmatter(fm, p, new_rel, default_domain, warnings)
        if warnings:
            report["fm_warnings"].append(f"{new_rel}: {', '.join(warnings)}")
        body = transform_body(body, old_rel, new_rel, moves, report)
        fm_text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=None).strip()
        out.write_text(f"---\n{fm_text}\n---\n{body.lstrip()}", encoding="utf-8")

    if not dry_run:
        write_report(dst, report)
    print(f"\nnotes: {report['notes']}  assets: {report['assets']}  "
          f"manual: {len(report['manual'])}  links remapped: {report['links_remapped']}  "
          f"unmapped: {len(report['links_unmapped'])}")
    if not dry_run:
        print(f"report: {dst / '00-inbox' / 'migration-report.md'}")
        print("next: python3 .scripts/validate_auxmem.py --all")


def write_report(dst: Path, r: dict):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "---",
        "title: Obsidian export import report",
        f"summary: obsidian-export pipeline import. {r['notes']} notes, "
        f"{r['links_remapped']} links remapped, {len(r['links_unmapped'])} unmapped, "
        f"{len(r['manual'])} files for manual handling, "
        f"{len(r['export_warnings']) // 2} unresolved links reported by obsidian-export.",
        "type: log", "status: active", f"domain: {REPORT_DOMAIN}",
        f"created: {today}", f"updated: {today}", "---", "",
        f"Dataview blocks stripped: {r['dataview_stripped']}. "
        f"Templater tags stripped: {r['templater_stripped']}.", "",
    ]
    for key, title in (("links_unmapped", "Unmapped link targets (now plain text)"),
                       ("export_warnings", "Unresolved links reported by obsidian-export"),
                       ("manual", "Files needing manual handling (00-inbox/import-manual/)"),
                       ("fm_warnings", "Frontmatter retrofits to review")):
        if r[key]:
            lines += [f"## {title}", ""] + [f"- {i}" for i in r[key]] + [""]
    out = dst / "00-inbox" / "migration-report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="obsidian-export output directory")
    ap.add_argument("--dst", required=True)
    ap.add_argument("--map", dest="map_file")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--auxmem-config", help="target auxmem .scripts/auxmem.config.json; sets valid domains")
    args = ap.parse_args()
    if args.auxmem_config:
        load_auxmem_domains(args.auxmem_config)
    src, dst = Path(args.src).expanduser(), Path(args.dst).expanduser()
    if not src.is_dir():
        sys.exit(f"export directory not found: {src}")
    run(src, dst, args.map_file, args.dry_run)


if __name__ == "__main__":
    main()
