# Setup

One-time setup for a corpus created from this template. Assumes Linux or WSL2. Commands use `~/my-corpus` as the corpus path; adjust as needed.

## 1. Prerequisites
- Python 3.10+ with PyYAML available to that interpreter.
- git.
- A POSIX shell or bash 3.2+. Koinome scripts use `#!/bin/bash` and are written for macOS default `/bin/bash` (3.2) and Linux bash; they do not require bash 4+, GNU coreutils, or `flock`.
- One or more CLI agents: Claude Code, Codex CLI, or Gemini CLI.
- Importing existing notes or seeding from AI exports is done from Koinome before or after creation, not from the corpus. See the starter docs/IMPORTING.md.

### Installing Koinome (includes PyYAML)

Supported paths:

```bash
# Editable dev install (this repository)
uv sync && uv run koinome --help

# End-user tool install
uv tool install koinome
pipx install koinome

# Wheel in a virtual environment
python3 -m venv .venv && source .venv/bin/activate
pip install koinome-*.whl
```

`./bootstrap.sh` checks for PyYAML but does **not** run `pip install` against system Python. If bootstrap reports a missing dependency, activate a venv or install Koinome via one of the paths above, then re-run bootstrap.

Paths containing spaces are supported (`koinome new --path "/path/with spaces/my-corpus"`).

On WSL2, keep the corpus on the Linux filesystem (`~/my-corpus`), not `/mnt/c`, for speed. You no longer need a Windows app to hold the files.

## 2. Copy and configure
```bash
cp -r koinome/template ~/my-corpus && cd ~/my-corpus
```
Edit `.scripts/koinome.config.json` if this corpus needs different domains. This file is the single source of truth. The `domains` map (folder to slug) drives folder creation, the `domain` frontmatter vocabulary, and MOC generation. Keep `type` and `status` closed unless you have a reason; they are the retrieval contract agents depend on. If you change domains after notes exist, see "Reconfiguring domains" below.

## 3. Bootstrap
```bash
./bootstrap.sh
```
This checks dependencies, creates domain and structural folders from the config, links provider skill directories to `.skills/`, initializes git, installs the pre-commit hook, generates MOCs, and runs the validator. It is idempotent; re-run it any time. After `koinome upgrade`, re-run `./bootstrap.sh` so the installed pre-commit hook picks up template fixes.

When symlinks are unavailable, bootstrap copies `.skills/` into provider directories and records them in `.koinome/skills-copies`. Copies do not update automatically when skills change — run `./bootstrap.sh --refresh-skills` after upgrading skills or the template.

## 4. Git remote
Use a private repository. This remote will hold your entire work context, so its access controls are part of your governance surface.
```bash
git remote add origin <your-private-repo-url>
git add -A && git commit -m "initial corpus"
git branch -M main
git push -u origin main
```

## 5. Agent configuration
- Claude Code: run `claude` from the corpus root. It reads CLAUDE.md automatically, which imports AGENTS.md. Skills in `.skills/` are linked to `.claude/skills/`.
- Codex CLI: reads AGENTS.md natively from the working directory. Skills are linked to `.codex/skills/`.
- Gemini CLI: set `contextFileName: "AGENTS.md"` in settings.json, or rely on the GEMINI.md stub. Skills are linked to `.gemini/skills/`.
- Cursor: skills are linked to `.cursor/skills/` (also reads `.claude/skills/` for compatibility).

After `koinome new`, run the `koinome-init` skill first to finish setup. Invoke skills explicitly (`/koinome-skill-name`) or let the agent match by description. Available workflows: init, domain setup, session close, validation fix, synthesis, new note, ADR, todo management, weekly review, seed distillation.

Prefer running one agent as the writer and others as readers, to reduce write-conflict and convention-drift risk across models.

## 6. Transparent git sync (optional but recommended)
The sync script commits, pulls with rebase, and pushes on a timer, with automatic conflict quarantine. See OPERATIONS.md for how it behaves.

On WSL2, enable systemd once (in `/etc/wsl.conf`):
```
[boot]
systemd=true
```
Then restart WSL (`wsl --shutdown` from Windows) and install the timer:
```bash
mkdir -p ~/.config/systemd/user
# split .scripts/koinome-sync.systemd into the two unit files per its header:
#   ~/.config/systemd/user/koinome-sync.service
#   ~/.config/systemd/user/koinome-sync.timer
systemctl --user daemon-reload
systemctl --user enable --now koinome-sync.timer
systemctl --user list-timers          # confirm it is scheduled
journalctl --user -u koinome-sync -f     # watch it run
```
If you do not want the timer, run `bash .scripts/koinome-sync.sh ~/my-corpus` manually or bind it to a shell alias.

## 7. Optional: editor link support
For link completion, go-to-definition, and rename-with-link-rewrite on plain markdown, install Marksman (an open-source markdown LSP) in VS Code, Neovim, Zed, or Helix. It covers most link-maintenance workflows on standard CommonMark links.

## Reconfiguring domains (after notes exist)
Changing `domains` in the config changes the valid `domain` vocabulary. Existing notes using an old slug will fail validation. Procedure:
1. Edit `.scripts/koinome.config.json` domains.
2. Update the `domain` field in any notes that used the old slugs (including seed notes in `60-decisions/`).
3. Run `python3 .scripts/gen_mocs.py` (prunes orphaned MOCs, builds new ones).
4. Run `python3 .scripts/validate_corpus.py --all` and fix any remaining violations.
5. Run `./bootstrap.sh` to create the new domain folders.

## Verify the install
```bash
python3 .scripts/validate_corpus.py --all   # should print "corpus validation clean."
git commit --allow-empty -m "test"          # hook should run
```
