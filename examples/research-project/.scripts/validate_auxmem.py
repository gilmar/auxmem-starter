#!/usr/bin/env python3
"""Auxmem guard: config-driven frontmatter, syntax, link, and todo.txt linter.

Reads .scripts/auxmem.config.json for controlled vocabularies and domain folders,
so the same script serves any auxmem built from this template.

Usage:
  validate_auxmem.py file1.md 72-tasks/todo.txt   # validate specific files (pre-commit)
  validate_auxmem.py --all               # validate the whole auxmem (CI)

Exit 0 = clean. Exit 1 = violations printed to stdout.
Requires: PyYAML (pip install pyyaml).
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

# ---------------------------------------------------------------- config ----

SCRIPT_DIR = Path(__file__).resolve().parent
AUXMEM_ROOT = SCRIPT_DIR.parent
CONFIG = json.loads((SCRIPT_DIR / "auxmem.config.json").read_text(encoding="utf-8"))

REQUIRED_FIELDS = CONFIG["required_fields"]
VOCAB = {
    "type": set(CONFIG["vocab"]["type"]),
    "status": set(CONFIG["vocab"]["status"]),
    "domain": set(CONFIG["domains"].values()),
}
MIN_SUMMARY_LEN = CONFIG.get("min_summary_len", 40)
SKIP_DIRS = set(CONFIG.get("skip_dirs", [".git", ".scripts", "90-templates", "99-archive"]))

# Non-standard syntax banned everywhere. Profile: CommonMark + GFM tables
# + YAML frontmatter + relative markdown links. Nothing else.
BANNED_PATTERNS = [
    (re.compile(r"!\[\[[^\]]+\]\]"), "wiki-style embed; use standard image/link syntax"),
    (re.compile(r"\[\[[^\]]+\]\]"), "wikilink; use a relative markdown link [title](path.md)"),
    (re.compile(r"^```\s*dataview(js)?\b", re.M), "dataview block; MOCs are generated, not queried"),
    (re.compile(r"`\$?=\s?[^`]+`"), "inline dataview expression"),
    (re.compile(r"<%[\s\S]*?%>"), "templater tag"),
    (re.compile(r"^\s*>\s*\[!\w+\]", re.M), "callout/alert syntax; use a plain blockquote"),
]

INTERNAL_LINK = re.compile(
    r"\[[^\]]*\]\((?!https?://|mailto:|#)([^)#]+?\.(?:md|pdf|png|jpg|jpeg|svg|csv))(#[^)]*)?\)"
)
FM_DELIM = re.compile(r"^---\s*$", re.M)
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# root-level meta files are not auxmem notes; they document the auxmem
META_FILES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md"}

# todo.txt grammar (http://todotxt.org/ spec)
TODO_DIR = Path("72-tasks")
TODO_FILES = {"todo.txt", "done.txt"}
TODO_DONE = re.compile(r"^x \d{4}-\d{2}-\d{2}( \d{4}-\d{2}-\d{2})? \S.*$")
TODO_OPEN = re.compile(r"^(\([A-Z]\) )?(\d{4}-\d{2}-\d{2} )?\S.*$")
TODO_BAD_PRI = re.compile(r"^\((?![A-Z]\) )[^)]*\)")
TODO_KV_DATE = re.compile(r"\b(due|t):(\S+)")


# ----------------------------------------------------------- YAML loader ---


class _RejectDuplicateKeysLoader(yaml.SafeLoader):
    pass


def _yaml_mapping_no_dupes(loader, node):
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate mapping key: {key!r}", key_node.start_mark
            )
        mapping[key] = loader.construct_object(value_node)
    return mapping


_RejectDuplicateKeysLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _yaml_mapping_no_dupes,
)


# ------------------------------------------------------------- path utils ---


def resolves_within_root(path: Path, root: Path) -> bool:
    """Return True when path resolves to a location inside root (follows symlinks)."""
    root_resolved = root.resolve()
    try:
        path.resolve(strict=False).relative_to(root_resolved)
        return True
    except ValueError:
        return False


def parse_iso_date(val) -> date | None:
    """Parse a YAML date or ISO date string; return None when invalid or impossible."""
    if isinstance(val, date):
        return val
    if not isinstance(val, str) or not ISO_DATE_RE.fullmatch(val.strip()):
        return None
    try:
        return date.fromisoformat(val.strip())
    except ValueError:
        return None


def resolve_note_target(raw: str, source: Path, root: Path) -> Path:
    """Resolve a markdown internal-link path relative to source and auxmem root."""
    decoded = raw.split("#", 1)[0].replace("%20", " ")
    if not decoded:
        return source
    if decoded.startswith("/"):
        return root / decoded.lstrip("/")
    candidate = Path(decoded)
    if candidate.is_absolute():
        return candidate
    return source.parent / decoded


def resolve_source_target(raw: str, root: Path) -> Path:
    """Resolve a synthesis source path (auxmem-root-relative, no leading slash)."""
    if Path(raw).is_absolute():
        return Path(raw)
    return root / raw


# ------------------------------------------------------------- validation ---


def split_frontmatter(text):
    if not text.startswith("---"):
        return None, "missing frontmatter block"
    parts = FM_DELIM.split(text, maxsplit=2)
    if len(parts) < 3:
        return None, "unterminated frontmatter block"
    try:
        fm = yaml.load(parts[1], Loader=_RejectDuplicateKeysLoader)
    except yaml.YAMLError as e:
        msg = str(e).strip()
        if "duplicate mapping key" in msg:
            return None, f"frontmatter has duplicate key ({msg})"
        return None, f"frontmatter is not valid YAML ({e.__class__.__name__})"
    if not isinstance(fm, dict):
        return None, "frontmatter is not a mapping"
    return fm, None


def check_frontmatter(fm):
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in fm or fm[field] in (None, "", []):
            errors.append(f"missing required field: {field}")
    for field, allowed in VOCAB.items():
        val = fm.get(field)
        if val is not None and val not in allowed:
            errors.append(
                f"{field}: '{val}' not in controlled vocabulary ({', '.join(sorted(allowed))})"
            )
    summary = fm.get("summary")
    if isinstance(summary, str) and 0 < len(summary.strip()) < MIN_SUMMARY_LEN:
        errors.append(
            f"summary too short ({len(summary.strip())} chars, min {MIN_SUMMARY_LEN}); "
            "front-load concrete nouns an agent would grep for"
        )
    for field in ("created", "updated", "generated_at"):
        val = fm.get(field)
        if val is None:
            continue
        if not parse_iso_date(val):
            errors.append(f"{field}: '{val}' is not a valid ISO date (YYYY-MM-DD)")
    if "tag" in fm:
        errors.append("use plural 'tags' with list syntax, not 'tag'")
    if fm.get("tags") is not None and not isinstance(fm.get("tags"), list):
        errors.append("tags must be a YAML list, e.g. tags: [semantic-layer]")
    errors.extend(check_synthesis(fm))
    return errors


SYNTHESIS_TYPES = {"entity", "concept"}
REVIEW_VALUES = {"needed", "approved"}


def check_synthesis(fm):
    """Enforce the raw/synthesized contract.
    - entity/concept pages must declare synthesis provenance.
    - anything marked synthesis: generated must cite sources.
    - authored notes must not claim to be generated.
    """
    errors = []
    typ = fm.get("type")
    synth = fm.get("synthesis")
    is_synth_type = typ in SYNTHESIS_TYPES

    if is_synth_type and synth != "generated":
        errors.append(f"type '{typ}' is a derived synthesis; it must set 'synthesis: generated'")
    if synth == "generated" and not is_synth_type:
        errors.append("authored notes must not set synthesis: generated; only entity/concept pages are derived")
    if synth is not None and synth != "generated":
        errors.append("synthesis: only value is 'generated' (or omit the field for authored notes)")

    if synth == "generated":
        review = fm.get("review")
        if review not in REVIEW_VALUES:
            errors.append(f"synthesized page needs review: {' or '.join(sorted(REVIEW_VALUES))}")
        gen = fm.get("generated_at")
        if not parse_iso_date(gen):
            errors.append("synthesized page needs generated_at: YYYY-MM-DD")
        sources = fm.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append("synthesized page must cite a non-empty 'sources' list (auxmem-root-relative paths)")
        else:
            for s in sources:
                if not isinstance(s, str):
                    errors.append(f"source entry must be a path string, got {type(s).__name__}")
                    continue
                errors.extend(_check_source_path(s))
    return errors


def _check_source_path(raw: str) -> list[str]:
    errors = []
    if Path(raw).is_absolute():
        errors.append(f"sources: absolute path not allowed -> {raw}")
        return errors
    target = resolve_source_target(raw, AUXMEM_ROOT)
    if not resolves_within_root(target, AUXMEM_ROOT):
        errors.append(f"sources: path escapes auxmem root -> {raw}")
        return errors
    if not target.exists():
        errors.append(f"sources: path does not resolve -> {raw}")
    return errors


def check_syntax(text):
    errors = []
    for pattern, label in BANNED_PATTERNS:
        m = pattern.search(text)
        if m:
            line = text.count("\n", 0, m.start()) + 1
            errors.append(f"line {line}: {label}")
    return errors


def check_links(text, path):
    errors = []
    for m in INTERNAL_LINK.finditer(text):
        raw = m.group(1)
        decoded = raw.replace("%20", " ")
        line = text.count("\n", 0, m.start()) + 1
        if Path(decoded).is_absolute() and not decoded.startswith("/"):
            errors.append(f"line {line}: absolute filesystem path not allowed -> {raw}")
            continue
        target = resolve_note_target(raw, path, AUXMEM_ROOT)
        if not resolves_within_root(target, AUXMEM_ROOT):
            errors.append(f"line {line}: link escapes auxmem root -> {raw}")
            continue
        if not target.exists():
            errors.append(f"line {line}: broken internal link -> {raw}")
    return errors


def check_todo(path):
    errors = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            errors.append(f"line {n}: blank line; one task per line, no gaps")
            continue
        if line != line.strip():
            errors.append(f"line {n}: leading/trailing whitespace")
            line = line.strip()
        if line.startswith("x ") or line == "x":
            if not TODO_DONE.match(line):
                errors.append(f"line {n}: completed task must be 'x YYYY-MM-DD [YYYY-MM-DD] description'")
        else:
            if line.lower().startswith("x "):
                errors.append(f"line {n}: completion marker must be lowercase 'x '")
            elif TODO_BAD_PRI.match(line):
                errors.append(f"line {n}: priority must be a single uppercase letter: (A) ")
            elif not TODO_OPEN.match(line):
                errors.append(f"line {n}: malformed task line")
            if path.name == "done.txt":
                errors.append(f"line {n}: done.txt must contain only completed (x) tasks")
        for key, val in TODO_KV_DATE.findall(line):
            if not parse_iso_date(val):
                errors.append(f"line {n}: {key}: value must be YYYY-MM-DD, got '{val}'")
    return errors


def validate_file(path):
    rel = path.resolve().relative_to(AUXMEM_ROOT)
    if rel.parts and rel.parts[0] in SKIP_DIRS:
        return []
    if len(rel.parts) == 1 and rel.name in META_FILES:
        return []
    if path.name in TODO_FILES:
        return check_todo(path)
    text = path.read_text(encoding="utf-8")
    errors = []
    fm, fm_err = split_frontmatter(text)
    if fm_err:
        errors.append(fm_err)
    else:
        errors.extend(check_frontmatter(fm))
    errors.extend(check_syntax(text))
    errors.extend(check_links(text, path))
    return errors


# ------------------------------------------------------------- fixability ---
# Classify an error string so an agent (or --json consumer) knows who fixes it.
#   auto   deterministic, no judgment (handled by --fix)
#   llm    needs content understanding; an agent drafts, a human accepts
#   human  genuinely ambiguous; the agent must ask before changing anything

def classify(err: str) -> str:
    if err.startswith("missing required field: updated") \
       or err.startswith("missing required field: created") \
       or err.startswith("use plural 'tags'") \
       or "is not a valid ISO date" in err \
       or err.startswith("tags must be a YAML list"):
        return "auto"
    if err.startswith("summary too short") \
       or err.startswith("missing required field: summary") \
       or err.startswith("missing required field: title") \
       or "synthesized page must cite" in err:
        return "llm"
    if "not in controlled vocabulary" in err \
       or err.startswith("missing required field: domain") \
       or "sources: path does not resolve" in err \
       or "sources: path escapes auxmem root" in err \
       or "sources: absolute path not allowed" in err \
       or "link escapes auxmem root" in err \
       or "absolute filesystem path not allowed" in err \
       or "authored notes must not set synthesis: generated" in err \
       or "duplicate key" in err \
       or "wikilink" in err or "embed" in err:
        return "human"
    return "llm"


def autofix_frontmatter(fm: dict) -> tuple[dict, list]:
    """Apply only the safe, judgment-free repairs. Returns (fm, changes)."""
    changes = []
    today = date.today().isoformat()
    # tag -> tags
    if "tag" in fm:
        val = fm.pop("tag")
        existing = fm.get("tags")
        merged = (existing if isinstance(existing, list) else []) + (
            val if isinstance(val, list) else [val])
        fm["tags"] = [t for t in merged if t]
        changes.append("renamed 'tag' to 'tags'")
    # tags string -> list
    if fm.get("tags") is not None and not isinstance(fm["tags"], list):
        fm["tags"] = [fm["tags"]]
        changes.append("wrapped 'tags' in a list")
    # zero-pad ISO-ish dates when the result is a real calendar date
    for field in ("created", "updated", "generated_at"):
        v = fm.get(field)
        if isinstance(v, str):
            m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", v.strip())
            if m and (len(m.group(2)) < 2 or len(m.group(3)) < 2):
                normalized = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
                if parse_iso_date(normalized):
                    fm[field] = normalized
                    changes.append(f"normalized {field} date format")
    # fill maintenance dates: updated defaults to today; created to updated-or-today
    if not fm.get("updated"):
        fm["updated"] = fm.get("created") or today
        changes.append("set missing 'updated' to today")
    if not fm.get("created"):
        fm["created"] = fm.get("updated") or today
        changes.append("set missing 'created'")
    return fm, changes


class _FMDumper(yaml.SafeDumper):
    pass


def _repr_list(dumper, value):
    # short scalar lists render inline (flow) so tags read like hand-authored frontmatter
    flow = len(value) <= 8 and all(isinstance(v, (str, int, float)) for v in value)
    return dumper.represent_sequence("tag:yaml.org,2002:seq", value, flow_style=flow)


_FMDumper.add_representer(list, _repr_list)


def _dump_frontmatter(fm: dict) -> str:
    return yaml.dump(
        fm, Dumper=_FMDumper, sort_keys=False, allow_unicode=True,
        default_flow_style=False, width=1000,
    ).rstrip()


def fix_file(path) -> list:
    """Rewrite a note applying autofix_frontmatter. Body is untouched. Returns changes."""
    rel = path.resolve().relative_to(AUXMEM_ROOT)
    if (rel.parts and rel.parts[0] in SKIP_DIRS) or path.name in TODO_FILES:
        return []
    if len(rel.parts) == 1 and rel.name in META_FILES:
        return []
    text = path.read_text(encoding="utf-8")
    fm, fm_err = split_frontmatter(text)
    if fm_err or fm is None:
        return []  # cannot safely fix a malformed/absent block
    fixed, changes = autofix_frontmatter(dict(fm))
    if not changes:
        return []
    parts = FM_DELIM.split(text, maxsplit=2)
    body = parts[2] if len(parts) >= 3 else ""
    path.write_text(f"---\n{_dump_frontmatter(fixed)}\n---{body}", encoding="utf-8")
    return changes


def _collect_files(argv):
    if "--all" in argv:
        return sorted(
            p for p in list(AUXMEM_ROOT.rglob("*.md"))
            + [AUXMEM_ROOT / TODO_DIR / f for f in TODO_FILES]
            if p.exists()
            and not any(part in SKIP_DIRS for part in p.relative_to(AUXMEM_ROOT).parts)
        )
    return [Path(a) for a in argv
            if a.endswith(".md") or Path(a).name in TODO_FILES]


def main(argv):
    files = _collect_files(argv)

    # --fix: apply deterministic repairs first, then fall through to validation
    if "--fix" in argv:
        total = []
        for f in files:
            if f.exists():
                for c in fix_file(f):
                    total.append((str(f), c))
        if "--json" not in argv:
            if total:
                print(f"auto-fixed {len(total)} item(s):")
                for fpath, c in total:
                    print(f"  {fpath}: {c}")
            else:
                print("nothing to auto-fix.")
            print()

    # gather remaining errors
    results = []
    for f in files:
        if not f.exists():
            continue
        try:
            errors = validate_file(f)
        except ValueError:
            continue
        if errors:
            results.append((str(f), errors))

    if "--json" in argv:
        payload = {
            "clean": not results,
            "files": [
                {
                    "file": fpath,
                    "errors": [
                        {"message": e, "fixable": classify(e)} for e in errs
                    ],
                }
                for fpath, errs in results
            ],
        }
        print(json.dumps(payload, indent=2))
        return 1 if results else 0

    if results:
        for fpath, errs in results:
            print(f"\n{fpath}")
            for e in errs:
                print(f"  - {e}  [{classify(e)}]")
        print(f"\n{len(results)} file(s) failed auxmem validation.")
        auto = sum(1 for _, errs in results for e in errs if classify(e) == "auto")
        if auto:
            print(f"{auto} item(s) are auto-fixable: run  python3 .scripts/validate_auxmem.py --fix --all")
        print("For the rest, ask your agent to fix them following docs/FIXING.md,")
        print("or fix by hand. Tags in brackets show who should fix each error.")
        return 1
    print("auxmem validation clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
