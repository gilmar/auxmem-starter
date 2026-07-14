"""Scaffold engine: create a new corpus from the bundled template.

Pure stdlib. Flag-driven and fully testable; the wizard calls into this.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from .bash_path import resolve_bash
from .corpus_identity import write_identity_manifest
from .line_endings import normalize_corpus_shell_scripts
from .version import TEMPLATE_VERSION

_PKG_ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = _PKG_ROOT / "template"
MANIFEST_SRC = TEMPLATE_DIR / ".koinome-manifest.json"

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FOLDER_RE = re.compile(r"^\d{2}-[a-z0-9-]+$")


class ScaffoldError(Exception):
    pass


def parse_domains(pairs):
    """pairs: list of 'NN-folder=slug' strings -> ordered dict folder->slug."""
    if not pairs:
        return {}
    domains = {}
    for p in pairs:
        if "=" not in p:
            raise ScaffoldError(f"domain must be 'NN-folder=slug', got '{p}'")
        folder, slug = (x.strip() for x in p.split("=", 1))
        if not FOLDER_RE.match(folder):
            raise ScaffoldError(f"folder '{folder}' must look like '10-projects' (NN-lowercase-hyphen)")
        if not SLUG_RE.match(slug):
            raise ScaffoldError(f"domain slug '{slug}' must be lowercase, digits, hyphens")
        domains[folder] = slug
    if not domains:
        raise ScaffoldError("at least one domain is required")
    return domains


def build_config(name, domains, base_config):
    cfg = json.loads(base_config)
    cfg["name"] = name
    cfg["created"] = date.today().isoformat()
    cfg["template_version"] = TEMPLATE_VERSION
    cfg["domains"] = domains
    return cfg


def write_corpus_state(dest):
    """Copy the manifest and a pristine snapshot of managed files into the corpus.
    The snapshot is the merge base for future `koinome upgrade` 3-way merges."""
    manifest = json.loads(MANIFEST_SRC.read_text(encoding="utf-8"))
    aux = Path(dest) / ".koinome"
    (aux / "snapshot").mkdir(parents=True, exist_ok=True)
    shutil.copy2(MANIFEST_SRC, aux / "manifest.json")
    for rel in manifest["files"]:
        src = TEMPLATE_DIR / rel
        snap = aux / "snapshot" / rel
        snap.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, snap)
    return manifest


def _substitute(path, replacements):
    text = path.read_text(encoding="utf-8")
    for token, val in replacements.items():
        text = text.replace(token, val)
    path.write_text(text, encoding="utf-8")


def scaffold(name, dest, domains, run_bootstrap=True, stream_bootstrap=False):
    """Create a corpus named `name` at `dest` with the given domain map."""
    if not TEMPLATE_DIR.is_dir():
        raise ScaffoldError(
            f"Koinome template not found at {TEMPLATE_DIR}. "
            "The installed package is missing template data; reinstall from the repo "
            "(python3 koinome-cli new) or upgrade Koinome."
        )
    dest = Path(dest).expanduser().resolve()
    if dest.exists() and any(dest.iterdir()):
        raise ScaffoldError(f"destination {dest} exists and is not empty")

    # copy template tree (dotfiles included)
    shutil.copytree(TEMPLATE_DIR, dest, dirs_exist_ok=True)
    # Git for Windows / some installs ship CRLF; bash then fails on pipefail/$'\r'.
    normalize_corpus_shell_scripts(dest)

    # write config from inputs
    base = (TEMPLATE_DIR / ".scripts" / "koinome.config.json").read_text(encoding="utf-8")
    cfg = build_config(name, domains, base)
    (dest / ".scripts" / "koinome.config.json").write_text(
        json.dumps(cfg, indent=2) + "\n", encoding="utf-8"
    )

    # placeholder substitution across seed content
    repl = {
        "__CORPUS_NAME__": name,
        "__TODAY__": date.today().isoformat(),
    }
    if domains:
        repl["__PRIMARY_DOMAIN__"] = next(iter(domains.values()))
    for rel in ("README.md", "72-tasks/todo.txt",
                "60-decisions/adr-0001-corpus-structure.md",
                "60-decisions/index.md"):
        p = dest / rel
        if p.exists():
            _substitute(p, repl)

    # ensure scripts are executable
    for script in (dest / ".scripts").glob("*.sh"):
        script.chmod(0o755)
    for script in (dest / ".scripts").glob("*.py"):
        script.chmod(0o755)
    (dest / "bootstrap.sh").chmod(0o755)

    # write the upgrade state: manifest + pristine snapshot (merge base)
    write_corpus_state(dest)
    write_identity_manifest(dest, corpus_name=name)

    result = {"dest": dest, "domains": domains, "bootstrapped": False}
    if run_bootstrap:
        bash = resolve_bash()
        # Prefer this interpreter: PATH's python3 often lacks PyYAML after tool install.
        env = {**os.environ, "KOINOME_PYTHON": sys.executable}
        kwargs = {"cwd": dest, "text": True, "env": env}
        if stream_bootstrap:
            proc = subprocess.run([bash, "bootstrap.sh"], **kwargs)
            result["bootstrap_stdout"] = ""
            result["bootstrap_stderr"] = ""
        else:
            proc = subprocess.run([bash, "bootstrap.sh"], capture_output=True, **kwargs)
            result["bootstrap_stdout"] = proc.stdout
            result["bootstrap_stderr"] = proc.stderr
        result["bootstrapped"] = proc.returncode == 0
        if proc.returncode != 0:
            detail = result["bootstrap_stdout"] + result["bootstrap_stderr"]
            raise ScaffoldError(
                f"bootstrap failed:\n{detail}" if detail.strip()
                else "bootstrap failed (see output above)"
            )
    return result
