# Usage

Full reference for the `corpus` command. Run in place with `./koinome-cli <cmd>` or install to get `corpus <cmd>`.

## Installing Koinome

Supported install paths (all include PyYAML):

```bash
# Development (this repository)
uv sync && uv run koinome --help

# End-user tool install
uv tool install koinome
pipx install koinome

# Wheel in a virtual environment
python3 -m venv .venv && source .venv/bin/activate
pip install corpus   # or: pip install dist/koinome-*.whl
```

`bootstrap.sh` inside a corpus checks for PyYAML but does not run `pip install` against system Python. If bootstrap reports a missing dependency, use one of the paths above, then re-run `./bootstrap.sh`. Paths containing spaces are supported (`koinome new --path "/path/with spaces/my-corpus"`).

When provider skill directories cannot be symlinked, bootstrap copies `.skills/` and records them in `.koinome/skills-copies`. Refresh copies after skill updates with `./bootstrap.sh --refresh-skills`. See `docs/RELEASE.md` for PyPI version policy before publishing.

## koinome new

Creates a corpus. Interactive when run bare; flag-driven when `--name` and `--path` are given.

### Interactive wizard
```bash
koinome new
```
A guided three-step flow: name, location, review. No subject domains are created — only shared structural folders (inbox, decisions, tasks, and so on). Your agent finishes setup with the `koinome-init` skill. Bootstrap progress prints live. The wizard requires a real terminal; in a pipe or CI it exits and tells you to use flags.

### Flag-driven (scriptable, CI-friendly)
```bash
koinome new --name my-work --path ~/my-work
```
Optional domains for scripts that already know the layout:
```bash
koinome new --name my-work --path ~/my-work \
  --domain 10-projects=projects \
  --domain 20-governance=governance
```
- `--name` lowercase letters, digits, hyphens.
- `--path` where to create it; must be empty or nonexistent.
- `--domain` optional, repeatable; `NN-folder=slug`. Folder is `NN-lowercase-hyphen`, slug is lowercase/digits/hyphens. Order matters: the first domain becomes the "primary" used by the seed ADR and initial tasks. Omit to leave domains empty for `koinome-init` to configure.
- `--no-bootstrap` skip folder/hook/MOC/validate setup (rarely needed).

### What creation does
Copies the template, writes `.scripts/koinome.config.json` from your inputs, substitutes the corpus name (and primary domain when `--domain` is given) into seed content, then runs the corpus's own `bootstrap.sh`: creates structural folders, links provider skill directories to `.skills/`, initializes git, installs the pre-commit hook, and — when domains are configured — generates MOCs and validates. a corpus with no domains skips MOC generation and validation until `koinome-init` runs.

## koinome seed

Stage 1 of seeding: normalize an AI provider export into a staging area outside any corpus.
```bash
koinome seed claude_conversations.json --staging ./seed-staging --since 2026-01-01
koinome seed chatgpt_conversations.json --staging ./seed-staging
koinome seed MyActivity.json --provider gemini --staging ./seed-staging --min-messages 3
```
- `--staging` where the corpus goes (outside the corpus; default `./seed-staging`).
- `--provider` force the provider if auto-detection is wrong.
- `--since` skip conversations before this date.
- `--min-messages` drop trivial conversations.

Stage 2 (distillation into notes) is an agent step. Point your CLI agent at `importers/distill-seeds.md` and run it from the target corpus. See `docs/IMPORTING.md`.

## koinome doctor

Validate a corpus and refresh its MOCs. Useful after manual edits or an import.
```bash
koinome doctor ~/my-work
```
Runs the target corpus's own `gen_mocs.py` then `validate_corpus.py --all`. Regenerates MOCs when stale.

## koinome check

Read-only conformance check: validation plus MOC freshness. Never modifies files. Use in CI.
```bash
koinome check ~/my-work
koinome check ~/my-work --manifest   # also verify managed tooling hashes
koinome check ~/my-work --git        # also require a clean git working tree
```

New corpora ship `.github/workflows/koinome-check.yml`, which runs `python3 .scripts/check_corpus.py` on each push and pull request.

## koinome upgrade

Migrate an existing corpus to the current template version. Safe to run anytime; it never touches your notes.
```bash
koinome upgrade ~/my-work
koinome upgrade ~/my-work --force   # re-apply even if already current
koinome upgrade ~/my-work --dry-run # preview changes without modifying files
```

Each corpus records the template version it was built from and keeps a pristine snapshot of managed files under `.koinome/`. Upgrade compares that to the current template and applies a per-file policy:

- **Tooling** (validator, hook, gen_mocs, sync, bootstrap): replaced with the new version. Your copy is backed up first, and if you had edited it the report says so.
- **Config** (`koinome.config.json`): structured merge. Your values (name, domains, and any scalar you set) are preserved; new schema keys and new vocabulary options are added. Reported line by line.
- **Guidance** (AGENTS.md, CLAUDE.md, GEMINI.md, README.md, docs, note templates): git 3-way merge against the snapshot. If you never edited a file, it updates cleanly. If you edited it and the template also changed it, you get either a clean merge or, where they truly collide, git conflict markers to resolve. corpora created before versioning have no snapshot, so those files are preserved and the new version is written beside them as `<file>.new` for manual merging.
- **Content** (your notes, `72-tasks/todo.txt`, `72-tasks/done.txt`, decisions, MOCs): never touched. MOCs are regenerated at the end.

If MOC generation or validation fails after upgrade, managed files are rolled back to their pre-upgrade state and a log is written under `.koinome/upgrade-failures/`. Merge conflicts are left for manual resolution and exit `2` (non-conformant). MOC generation failures exit `1` (operation failure).

### Exit codes

| code | meaning |
| --- | --- |
| `0` | success; corpus is conformant when validation ran |
| `1` | usage error, subprocess failure, or other operation error |
| `2` | operation completed but the corpus failed validation |
| `3` | conflict or quarantine created (reserved for sync) |

After upgrade, run `./bootstrap.sh` from the corpus root so `.git/hooks/pre-commit` is refreshed from `.scripts/pre-commit` (upgrade updates the source file but does not reinstall the hook).

### Migrating task files to 72-tasks/ (template 1.1.0+)

Task files moved from the corpus root into `72-tasks/`. Upgrade updates tooling and config but does not move your content. If Your corpus still has root-level task files:
```bash
mkdir -p 72-tasks
git mv todo.txt 72-tasks/todo.txt
[ -f done.txt ] && git mv done.txt 72-tasks/done.txt
./bootstrap.sh
```

### Adopting agent skills (template 1.2.0+)

Template 1.2.0 adds `.skills/` (provider-agnostic Agent Skills) and links them into `.claude/skills`, `.codex/skills`, `.gemini/skills`, and `.cursor/skills`. After `koinome upgrade`, run `./bootstrap.sh` once to create the symlinks. Upgrade delivers the skill files via 3-way merge; re-run bootstrap if provider dirs are missing.

### Cutting a new template version (maintainer)
1. Edit files under `koinome/template/`.
2. Bump `koinome/version.py` (`TEMPLATE_VERSION`).
3. Run `python3 build_manifest.py` to regenerate `koinome/template/.koinome-manifest.json`.
4. Commit. corpora adopt the change on their next `koinome upgrade`.

New files are classified automatically by path (`build_manifest.py` `policy_for`): `.scripts/` and `bootstrap.sh` are tooling, `koinome.config.json` is merge, top-level guidance, `docs/*.md`, `90-templates/*.md`, and `.skills/**` are 3-way, everything else is user content and stays unmanaged.

## Adding or changing domains

After `koinome new`, point your agent at the corpus and run the `koinome-init` skill. It orients you, sets up domains (or confirms pre-set ones), and finishes first-run setup.

To change domains later, run the `koinome-setup-domains` skill or edit the corpus's `.scripts/koinome.config.json` `domains` map manually, update any notes using removed slugs, then from the corpus run `./bootstrap.sh`, `python3 .scripts/gen_mocs.py`, and `python3 .scripts/validate_corpus.py --all`. See the corpus's `docs/SETUP.md` (Reconfiguring domains).
