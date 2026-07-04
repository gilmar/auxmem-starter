"""Interactive terminal wizard for `auxmem new`.

Stdlib only. Sequential validated prompts with a confirmation screen. Falls
back cleanly if stdin is not a tty (raises so the CLI can tell the user to use
flags instead).
"""

import sys
from pathlib import Path

from . import scaffold

CLEAR = "\033[2J\033[H"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _banner():
    print(f"{BOLD}auxmem{RESET} {DIM}. create a new auxiliary-memory vault{RESET}\n")


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
        return "use lowercase letters, digits, and hyphens (e.g. my-work-vault)"
    return None


def run():
    if not sys.stdin.isatty():
        raise scaffold.ScaffoldError(
            "no interactive terminal; use flags: auxmem new --name NAME --path PATH --domain NN-folder=slug ..."
        )
    print(CLEAR, end="")
    _banner()

    name = _ask("Vault name", default="my-vault", validate=_validate_name)
    default_path = str(Path.home() / name)
    path = _ask("Path to create it at", default=default_path)

    print(f"\n{DIM}Domains are your subject-matter folders. Format: NN-folder=slug.")
    print(f"Enter one per line. Blank line when done. Example: 10-projects=projects{RESET}")
    domains = {}
    n = len(domains)
    suggested = ["10-", "20-", "30-", "40-", "50-"]
    while True:
        idx = len(domains)
        hint = suggested[idx] if idx < len(suggested) else f"{(idx + 1) * 10}-"
        raw = input(f"  domain {idx + 1} ({DIM}e.g. {hint}name=slug{RESET}, blank to finish): ").strip()
        if not raw:
            if domains:
                break
            print("  at least one domain is required.")
            continue
        try:
            domains.update(scaffold.parse_domains([raw]))
        except scaffold.ScaffoldError as e:
            print(f"  {e}")

    seed = _yesno("\nSeed or import into this vault after creating it?", default=False)

    # confirmation screen
    print(f"\n{BOLD}About to create:{RESET}")
    print(f"  name    {name}")
    print(f"  path    {path}")
    print(f"  domains")
    for folder, slug in domains.items():
        print(f"          {folder}  ->  {slug}")
    print(f"  then    {'show import instructions' if seed else 'ready to use'}")
    if not _yesno("\nProceed?", default=True):
        print("cancelled.")
        return None

    result = scaffold.scaffold(name, path, domains, run_bootstrap=True)
    print(f"\n{BOLD}Created {result['dest']}{RESET}")
    print("Next steps:")
    print(f"  cd {result['dest']}")
    print("  git remote add origin <your-private-repo-url>")
    print("  git add -A && git commit -m 'initial vault' && git push -u origin main")
    if seed:
        print("\nTo seed or import, from the auxmem-starter directory:")
        print(f"  auxmem seed <export.json> --staging ./seed-staging")
        print(f"  auxmem import-obsidian <old-vault> --dest {result['dest']} --map map.json")
        print("  see docs/IMPORTING.md")
    return result
