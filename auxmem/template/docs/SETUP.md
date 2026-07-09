# Setup

One-time setup for a vault created from this template. Assumes Linux or WSL2. Commands use `~/vault` as the vault path; adjust as needed.

## 1. Prerequisites
- Python 3.10+ with pip.
- git.
- One or more CLI agents: Claude Code, Codex CLI, or Gemini CLI.
- Importing existing notes or seeding from AI exports is done from auxmem-starter before or after creation, not from the vault. See the starter docs/IMPORTING.md.

On WSL2, keep the vault on the Linux filesystem (`~/vault`), not `/mnt/c`, for speed. You no longer need a Windows app to hold the files.

## 2. Copy and configure
```bash
cp -r vault-template ~/vault && cd ~/vault
```
Edit `.scripts/vault.config.json` if this vault needs different domains. This file is the single source of truth. The `domains` map (folder to slug) drives folder creation, the `domain` frontmatter vocabulary, and MOC generation. Keep `type` and `status` closed unless you have a reason; they are the retrieval contract agents depend on. If you change domains after notes exist, see "Reconfiguring domains" below.

## 3. Bootstrap
```bash
./bootstrap.sh
```
This checks dependencies, creates domain and structural folders from the config, links provider skill directories to `.skills/`, initializes git, installs the pre-commit hook, generates MOCs, and runs the validator. It is idempotent; re-run it any time.

## 4. Git remote
Use a private repository. This remote will hold your entire work context, so its access controls are part of your governance surface.
```bash
git remote add origin <your-private-repo-url>
git add -A && git commit -m "initial vault"
git branch -M main
git push -u origin main
```

## 5. Agent configuration
- Claude Code: run `claude` from the vault root. It reads CLAUDE.md automatically, which imports AGENTS.md. Skills in `.skills/` are linked to `.claude/skills/`.
- Codex CLI: reads AGENTS.md natively from the working directory. Skills are linked to `.codex/skills/`.
- Gemini CLI: set `contextFileName: "AGENTS.md"` in settings.json, or rely on the GEMINI.md stub. Skills are linked to `.gemini/skills/`.
- Cursor: skills are linked to `.cursor/skills/` (also reads `.claude/skills/` for compatibility).

Invoke skills explicitly (`/skill-name`) or let the agent match by description. Available workflows: session close, validation fix, synthesis, new note, ADR, todo management, weekly review, seed distillation.

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
# split .scripts/vault-sync.systemd into the two unit files per its header:
#   ~/.config/systemd/user/vault-sync.service
#   ~/.config/systemd/user/vault-sync.timer
systemctl --user daemon-reload
systemctl --user enable --now vault-sync.timer
systemctl --user list-timers          # confirm it is scheduled
journalctl --user -u vault-sync -f     # watch it run
```
If you do not want the timer, run `bash .scripts/vault-sync.sh ~/vault` manually or bind it to a shell alias.

## 7. Optional: editor link support
For link completion, go-to-definition, and rename-with-link-rewrite on plain markdown, install Marksman (an open-source markdown LSP) in VS Code, Neovim, Zed, or Helix. It replaces most of what Obsidian did for link maintenance, on standard CommonMark links.

## Reconfiguring domains (after notes exist)
Changing `domains` in the config changes the valid `domain` vocabulary. Existing notes using an old slug will fail validation. Procedure:
1. Edit `.scripts/vault.config.json` domains.
2. Update the `domain` field in any notes that used the old slugs (including seed notes in `60-decisions/`).
3. Run `python3 .scripts/gen_mocs.py` (prunes orphaned MOCs, builds new ones).
4. Run `python3 .scripts/validate_vault.py --all` and fix any remaining violations.
5. Run `./bootstrap.sh` to create the new domain folders.

## Verify the install
```bash
python3 .scripts/validate_vault.py --all   # should print "vault validation clean."
git commit --allow-empty -m "test"          # hook should run
```
