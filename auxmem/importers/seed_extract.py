#!/usr/bin/env python3
"""seed_extract.py: normalize AI provider data exports into a staging corpus.

Parses official data exports from Claude (claude.ai), ChatGPT, and Gemini
(Google Takeout) into one markdown file per conversation, with frontmatter,
under a staging directory OUTSIDE the auxmem. A CLI agent then distills the
staging corpus into auxmem seed notes (see distill-seeds.md).

Usage:
  seed_extract.py <export_file.json> [--out seed-staging] [--since YYYY-MM-DD]
                  [--min-messages N] [--provider claude|chatgpt|gemini]

Provider is auto-detected from the JSON structure unless --provider is given.
Stdlib only. Run once per export file; safe to re-run (files overwritten).
"""

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

MAX_SLUG = 60


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "untitled").lower()).strip("-")
    return s[:MAX_SLUG].rstrip("-") or "untitled"


def iso_day(ts) -> str:
    """Accept ISO strings or epoch floats; return YYYY-MM-DD."""
    if ts is None:
        return "unknown-date"
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    return str(ts)[:10]


def detect_provider(data) -> str:
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            if "chat_messages" in first:
                return "claude"
            if "mapping" in first:
                return "chatgpt"
            if first.get("header") == "Gemini Apps" or "Gemini" in str(first.get("header", "")):
                return "gemini"
    raise SystemExit("Could not auto-detect provider; pass --provider explicitly.")


# ------------------------------------------------------------- extractors ---


def _claude_text(m):
    """Text from a Claude message: prefer the flat 'text', else concatenate
    text blocks from the structured 'content' array."""
    if isinstance(m.get("text"), str) and m["text"].strip():
        parts = [m["text"]]
    else:
        parts = []
        for p in m.get("content", []) or []:
            if not isinstance(p, dict):
                continue
            if p.get("type") == "text" and isinstance(p.get("text"), str):
                parts.append(p["text"])
            elif p.get("type") in ("tool_use", "tool_result"):
                continue  # skip tool plumbing
    # note attachments/files by name so context is not silently lost
    for a in m.get("attachments", []) or []:
        name = a.get("file_name") or a.get("name")
        if name:
            parts.append(f"[attachment: {name}]")
    return "\n".join(x for x in parts if isinstance(x, str) and x.strip())


def extract_claude(data) -> list[dict]:
    convos = []
    for c in data:
        messages = []
        for m in c.get("chat_messages", []):
            if not isinstance(m, dict):
                continue
            text = _claude_text(m)
            if text.strip():
                role = "user" if m.get("sender") == "human" else "assistant"
                messages.append((role, text.strip()))
        convos.append({
            "title": (c.get("name") or "").strip() or "Untitled",
            "date": iso_day(c.get("created_at")),
            "updated": iso_day(c.get("updated_at") or c.get("created_at")),
            "messages": messages,
        })
    return convos


def _chatgpt_text(content):
    """Extract text from a ChatGPT message content block across the content
    types seen in real exports. Returns '' if nothing textual."""
    if not isinstance(content, dict):
        return ""
    ctype = content.get("content_type")
    if ctype == "text":
        parts = content.get("parts", [])
        return "\n".join(p for p in parts if isinstance(p, str))
    if ctype == "multimodal_text":
        # parts mix strings and asset-pointer dicts (images, files)
        out = []
        for p in content.get("parts", []):
            if isinstance(p, str):
                out.append(p)
            elif isinstance(p, dict):
                out.append(f"[{p.get('content_type', 'attachment')}]")
        return "\n".join(x for x in out if x)
    if ctype == "code":
        return content.get("text", "") or ""
    if ctype == "execution_output":
        return content.get("text", "") or ""
    if ctype in ("tether_quote", "tether_browsing_display"):
        return content.get("text") or content.get("result", "") or ""
    # user_editable_context (custom instructions), system_error, etc.: skip
    return ""


def extract_chatgpt(data) -> list[dict]:
    convos = []
    for c in data:
        mapping = c.get("mapping", {})
        # Walk from current_node to root: this is the surviving branch after any
        # edits/regenerations. Earlier branches are intentionally not exported as
        # the canonical thread.
        chain, node_id, seen = [], c.get("current_node"), set()
        while node_id and node_id in mapping and node_id not in seen:
            seen.add(node_id)  # guard against malformed cyclic parents
            node = mapping[node_id]
            msg = node.get("message")
            if msg:
                chain.append(msg)
            node_id = node.get("parent")
        # fallback: some exports lack current_node; use insertion order
        if not chain:
            chain = [n["message"] for n in mapping.values()
                     if isinstance(n, dict) and n.get("message")]
        else:
            chain.reverse()

        messages = []
        for msg in chain:
            if not isinstance(msg, dict):
                continue
            role = (msg.get("author") or {}).get("role")
            if role not in ("user", "assistant"):
                continue  # drop system/tool
            # skip hidden/system messages that ChatGPT injects
            meta = msg.get("metadata") or {}
            if meta.get("is_visually_hidden_from_conversation"):
                continue
            text = _chatgpt_text(msg.get("content") or {})
            if text.strip():
                messages.append((role, text.strip()))

        convos.append({
            "title": (c.get("title") or "").strip() or "Untitled",
            "date": iso_day(c.get("create_time")),
            "updated": iso_day(c.get("update_time") or c.get("create_time")),
            "messages": messages,
        })
    return convos


def extract_gemini(data) -> list[dict]:
    """Takeout MyActivity gives prompts only. Group them into daily logs."""
    by_day = defaultdict(list)
    for item in data:
        title = item.get("title", "")
        prompt = title[len("Prompted "):] if title.startswith("Prompted ") else title
        if prompt.strip():
            by_day[iso_day(item.get("time"))].append(prompt.strip())
    return [
        {
            "title": "Gemini prompts",
            "date": day,
            "updated": day,
            "messages": [("user", p) for p in prompts],
        }
        for day, prompts in sorted(by_day.items())
    ]


EXTRACTORS = {"claude": extract_claude, "chatgpt": extract_chatgpt, "gemini": extract_gemini}

# ------------------------------------------------------------------ write ---


def _yaml_safe(s: str) -> str:
    """Quote a scalar for YAML if it could break parsing."""
    s = s.replace("\n", " ").strip()
    if s == "" or s[0] in "!&*?|>%@`\"'#[]{},:" or ": " in s or s.endswith(":"):
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return s


def _cell(s: str) -> str:
    """Escape a value for a GFM table cell."""
    return s.replace("\n", " ").replace("|", "\\|").strip()


def write_corpus(convos, provider: str, out_dir: Path, since: str, min_messages: int):
    pdir = out_dir / provider
    pdir.mkdir(parents=True, exist_ok=True)
    index_rows, written, taken = [], 0, set()
    for c in convos:
        if c["date"] != "unknown-date" and c["date"] < since:
            continue
        if len(c["messages"]) < min_messages:
            continue  # drops empty/trivial conversations
        stem = f"{c['date']}-{slugify(c['title'])}"
        fname = stem + ".md"
        n = 2
        while fname in taken:  # deterministic collision suffixing, no file re-reads
            fname = f"{stem}-{n}.md"
            n += 1
        taken.add(fname)
        path = pdir / fname
        body = [
            "---",
            f"title: {_yaml_safe(c['title'])}",
            f"provider: {provider}",
            f"date: {c['date']}",
            f"updated: {c['updated']}",
            f"message_count: {len(c['messages'])}",
            "---",
            "",
        ]
        for role, text in c["messages"]:
            body.append(f"## {role}")
            body.append("")
            body.append(text)
            body.append("")
        path.write_text("\n".join(body), encoding="utf-8")
        index_rows.append((c["updated"], c["title"], f"{provider}/{fname}", len(c["messages"])))
        written += 1

    # append to the shared triage index
    index = out_dir / "index.md"
    lines = index.read_text(encoding="utf-8").splitlines() if index.exists() else [
        "# Staging corpus index",
        "",
        "| updated | title | file | msgs |",
        "|---|---|---|---|",
    ]
    existing = set(lines)
    for updated, title, rel, count in sorted(index_rows, reverse=True):
        row = f"| {updated} | {_cell(title)} | {rel} | {count} |"
        if row not in existing:
            lines.append(row)
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export_file")
    ap.add_argument("--out", default="seed-staging")
    ap.add_argument("--since", default="0000-00-00", help="skip conversations before this date")
    ap.add_argument("--min-messages", type=int, default=2)
    ap.add_argument("--provider", choices=list(EXTRACTORS))
    args = ap.parse_args()

    data = json.loads(Path(args.export_file).read_text(encoding="utf-8"))
    provider = args.provider or detect_provider(data)
    convos = EXTRACTORS[provider](data)
    written = write_corpus(convos, provider, Path(args.out), args.since, args.min_messages)
    print(f"{provider}: {written} conversation file(s) written to {args.out}/{provider}/")
    print(f"triage index: {args.out}/index.md")


if __name__ == "__main__":
    main()
