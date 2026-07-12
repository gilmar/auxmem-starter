"""Interactive terminal wizard for `auxmem new`.

Stdlib only. Guided steps with plain-language context, a creation preview,
and live bootstrap progress. Falls back cleanly if stdin is not a tty (raises
so the CLI can tell the user to use flags instead).
"""

import json
import sys
from pathlib import Path

from . import scaffold

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

STRUCTURAL_NOTES = {
    "00-inbox": "unsorted captures",
    "05-sources": "raw intake, synthesis queue",
    "60-decisions": "decision log (ADRs)",
    "70-meetings": "meeting notes",
    "71-log": "session logs",
    "72-tasks": "todo.txt task list",
    "80-moc": "generated maps of content",
    "85-synthesis": "derived pages with provenance",
    "90-templates": "note templates",
    "95-assets": "images and binaries",
    "99-archive": "stale content, do not search",
}


def _banner():
    print(f"{BOLD}auxmem{RESET} {DIM}create a governed memory folder for your AI agents{RESET}\n")
    print(
        "You are about to create an auxmem: a folder of plain markdown notes with a "
        "validator, a git hook, and agent skills. Your agents read and write it; "
        "nothing runs in the background.\n"
    )


def _step(n, total, title):
    print(f"{BOLD}Step {n}/{total}: {title}{RESET}")


def _ask(prompt, default=None, validate=None):
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{suffix}: ").strip()
        if not raw and default is not None:
            raw = default
        if not raw:
            print("  required.")
            continue
        if validate:
            err = validate(raw)
            if err:
                print(f"  {err}")
                continue
        return raw


def _yesno(prompt, default=True):
    d = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{prompt} [{d}]: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  answer y or n.")


def _validate_name(v):
    if not scaffold.SLUG_RE.match(v):
        return "use lowercase letters, digits, and hyphens (e.g. my-work)"
    return None


def _template_structural_folders():
    cfg_path = scaffold.TEMPLATE_DIR / ".scripts" / "auxmem.config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    return cfg.get("structural_folders", [])


def _show_preview(name, path):
    print(f"\n{BOLD}this auxmem will contain:{RESET}\n")
    print(f"  {DIM}name{RESET}     {name}")
    print(f"  {DIM}path{RESET}     {path}")
    print(
        f"\n  {DIM}subject domains{RESET}  "
        f"{DIM}none yet — auxmem-init will define them with you{RESET}"
    )
    print(f"\n  {DIM}shared structure{RESET} (same in every auxmem)")
    for folder in _template_structural_folders():
        note = STRUCTURAL_NOTES.get(folder, "")
        suffix = f"  {DIM}{note}{RESET}" if note else ""
        print(f"    {folder}/{suffix}")
    print(f"\n  {DIM}tooling installed{RESET}")
    print("    git repo, validation hook, generated navigation")
    print("    agent skills linked for Claude Code, Codex, Gemini CLI, and Cursor")
    print("    AGENTS.md as the canonical guide for every agent\n")


def run():
    if not sys.stdin.isatty():
        raise scaffold.ScaffoldError(
            "no interactive terminal; use flags: auxmem new --name NAME --path PATH "
            "[--domain NN-folder=slug ...]"
        )

    _banner()
    total = 3

    _step(1, total, "Name your auxmem")
    print(
        f"{DIM}Used as the auxmem label, git repo name, and in config. "
        "Lowercase and hyphens only.{RESET}\n"
    )
    name = _ask("Auxmem name", default="my-auxmem", validate=_validate_name)

    _step(2, total, "Choose a location")
    print(f"{DIM}Must be empty or not exist yet.{RESET}\n")
    default_path = str(Path.home() / name)
    path = _ask("Path", default=default_path)

    _step(3, total, "Review and create")
    _show_preview(name, path)
    if not _yesno("Create this auxmem?", default=True):
        print("cancelled.")
        return None

    print(f"\n{BOLD}Creating auxmem...{RESET}\n")
    result = scaffold.scaffold(
        name, path, {}, run_bootstrap=True, stream_bootstrap=True
    )

    dest = result["dest"]
    print(f"\n{BOLD}Auxmem ready at {dest}{RESET}\n")
    print("Next steps:")
    print(f"  1. cd {dest}")
    print("  2. Point your agent at this folder (claude, codex, or gemini)")
    print("     Run the auxmem-init skill — it interviews you, sets up domains, and finishes setup.")
    print("  3. Optional: set a private git remote and push")
    print("     git remote add origin <url>")
    print("     git add -A && git commit -m 'initial auxmem' && git push -u origin main")
    print("  4. Optional: seed from AI exports (see docs/IMPORTING.md)")
    print("     auxmem seed <export.json> --staging ./seed-staging")
    return result
