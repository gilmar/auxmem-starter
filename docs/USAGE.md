# Usage

Full reference for the `auxmem` command. Run in place with `./auxmem-cli <cmd>` or install to get `auxmem <cmd>`.

## Installing AuxMem

Supported install paths (all include PyYAML):

```bash
# Development (this repository)
uv sync && uv run auxmem --help

# End-user tool install
uv tool install auxmem
pipx install auxmem

# Wheel in a virtual environment
python3 -m venv .venv && source .venv/bin/activate
pip install auxmem   # or: pip install dist/auxmem-*.whl
```

`bootstrap.sh` inside an auxmem checks for PyYAML but does not run `pip install` against system Python. If bootstrap reports a missing dependency, use one of the paths above, then re-run `./bootstrap.sh`. Paths containing spaces are supported (`auxmem new --path "/path/with spaces/my-auxmem"`).

When provider skill directories cannot be symlinked, bootstrap copies `.skills/` and records them in `.auxmem/skills-copies`. Refresh copies after skill updates with `./bootstrap.sh --refresh-skills`. See `docs/RELEASE.md` for PyPI version policy before publishing.

## auxmem new

Creates an auxmem. Interactive when run bare; flag-driven when `--name` and `--path` are given.

### Interactive wizard
```bash
auxmem new
```
A guided three-step flow: name, location, review. No subject domains are created — only shared structural folders (inbox, decisions, tasks, and so on). Your agent finishes setup with the `auxmem-init` skill. Bootstrap progress prints live. The wizard requires a real terminal; in a pipe or CI it exits and tells you to use flags.

### Flag-driven (scriptable, CI-friendly)
```bash
auxmem new --name my-work --path ~/my-work
```
Optional domains for scripts that already know the layout:
```bash
auxmem new --name my-work --path ~/my-work \
  --domain 10-projects=projects \
  --domain 20-governance=governance
```
- `--name` lowercase letters, digits, hyphens.
- `--path` where to create it; must be empty or nonexistent.
- `--domain` optional, repeatable; `NN-folder=slug`. Folder is `NN-lowercase-hyphen`, slug is lowercase/digits/hyphens. Order matters: the first domain becomes the "primary" used by the seed ADR and initial tasks. Omit to leave domains empty for `auxmem-init` to configure.
- `--no-bootstrap` skip folder/hook/MOC/validate setup (rarely needed).

### What creation does
Copies the template, writes `.scripts/auxmem.config.json` from your inputs, substitutes the auxmem name (and primary domain when `--domain` is given) into seed content, then runs the auxmem's own `bootstrap.sh`: creates structural folders, links provider skill directories to `.skills/`, initializes git, installs the pre-commit hook, and — when domains are configured — generates MOCs and validates. An auxmem with no domains skips MOC generation and validation until `auxmem-init` runs.

## auxmem seed

Stage 1 of seeding: normalize an AI provider export into a staging corpus outside any auxmem.
```bash
auxmem seed claude_conversations.json --staging ./seed-staging --since 2026-01-01
auxmem seed chatgpt_conversations.json --staging ./seed-staging
auxmem seed MyActivity.json --provider gemini --staging ./seed-staging --min-messages 3
```
- `--staging` where the corpus goes (outside the auxmem; default `./seed-staging`).
- `--provider` force the provider if auto-detection is wrong.
- `--since` skip conversations before this date.
- `--min-messages` drop trivial conversations.

Stage 2 (distillation into notes) is an agent step. Point your CLI agent at `importers/distill-seeds.md` and run it from the target auxmem. See `docs/IMPORTING.md`.

## auxmem doctor

Validate an auxmem and refresh its MOCs. Useful after manual edits or an import.
```bash
auxmem doctor ~/my-work
```
Runs the target auxmem's own `gen_mocs.py` then `validate_auxmem.py --all`. Regenerates MOCs when stale.

## auxmem check

Read-only conformance check: validation plus MOC freshness. Never modifies files. Use in CI.
```bash
auxmem check ~/my-work
auxmem check ~/my-work --manifest   # also verify managed tooling hashes
auxmem check ~/my-work --git        # also require a clean git working tree
```

New auxmems ship `.github/workflows/auxmem-check.yml`, which runs `python3 .scripts/check_auxmem.py` on each push and pull request.

## auxmem upgrade

Migrate an existing auxmem to the current template version. Safe to run anytime; it never touches your notes.
```bash
auxmem upgrade ~/my-work
auxmem upgrade ~/my-work --force   # re-apply even if already current
auxmem upgrade ~/my-work --dry-run # preview changes without modifying files
```

Each auxmem records the template version it was built from and keeps a pristine snapshot of managed files under `.auxmem/`. Upgrade compares that to the current template and applies a per-file policy:

- **Tooling** (validator, hook, gen_mocs, sync, bootstrap): replaced with the new version. Your copy is backed up first, and if you had edited it the report says so.
- **Config** (`auxmem.config.json`): structured merge. Your values (name, domains, and any scalar you set) are preserved; new schema keys and new vocabulary options are added. Reported line by line.
- **Guidance** (AGENTS.md, CLAUDE.md, GEMINI.md, README.md, docs, note templates): git 3-way merge against the snapshot. If you never edited a file, it updates cleanly. If you edited it and the template also changed it, you get either a clean merge or, where they truly collide, git conflict markers to resolve. Auxmems created before versioning have no snapshot, so those files are preserved and the new version is written beside them as `<file>.new` for manual merging.
- **Content** (your notes, `72-tasks/todo.txt`, `72-tasks/done.txt`, decisions, MOCs): never touched. MOCs are regenerated at the end.

If MOC generation or validation fails after upgrade, managed files are rolled back to their pre-upgrade state and a log is written under `.auxmem/upgrade-failures/`. Merge conflicts are left for manual resolution and exit `2` (non-conformant). MOC generation failures exit `1` (operation failure).

### Exit codes

| code | meaning |
| --- | --- |
| `0` | success; auxmem is conformant when validation ran |
| `1` | usage error, subprocess failure, or other operation error |
| `2` | operation completed but the auxmem failed validation |
| `3` | conflict or quarantine created (reserved for sync) |

After upgrade, run `./bootstrap.sh` from the auxmem root so `.git/hooks/pre-commit` is refreshed from `.scripts/pre-commit` (upgrade updates the source file but does not reinstall the hook).

### Migrating task files to 72-tasks/ (template 1.1.0+)

Task files moved from the auxmem root into `72-tasks/`. Upgrade updates tooling and config but does not move your content. If your auxmem still has root-level task files:
```bash
mkdir -p 72-tasks
git mv todo.txt 72-tasks/todo.txt
[ -f done.txt ] && git mv done.txt 72-tasks/done.txt
./bootstrap.sh
```

### Adopting agent skills (template 1.2.0+)

Template 1.2.0 adds `.skills/` (provider-agnostic Agent Skills) and links them into `.claude/skills`, `.codex/skills`, `.gemini/skills`, and `.cursor/skills`. After `auxmem upgrade`, run `./bootstrap.sh` once to create the symlinks. Upgrade delivers the skill files via 3-way merge; re-run bootstrap if provider dirs are missing.

### Cutting a new template version (maintainer)
1. Edit files under `auxmem/template/`.
2. Bump `auxmem/version.py` (`TEMPLATE_VERSION`).
3. Run `python3 build_manifest.py` to regenerate `auxmem/template/.auxmem-manifest.json`.
4. Commit. Auxmems adopt the change on their next `auxmem upgrade`.

New files are classified automatically by path (`build_manifest.py` `policy_for`): `.scripts/` and `bootstrap.sh` are tooling, `auxmem.config.json` is merge, top-level guidance, `docs/*.md`, `90-templates/*.md`, and `.skills/**` are 3-way, everything else is user content and stays unmanaged.

## Adding or changing domains

After `auxmem new`, point your agent at the auxmem and run the `auxmem-init` skill. It orients you, sets up domains (or confirms pre-set ones), and finishes first-run setup.

To change domains later, run the `auxmem-setup-domains` skill or edit the auxmem's `.scripts/auxmem.config.json` `domains` map manually, update any notes using removed slugs, then from the auxmem run `./bootstrap.sh`, `python3 .scripts/gen_mocs.py`, and `python3 .scripts/validate_auxmem.py --all`. See the auxmem's `docs/SETUP.md` (Reconfiguring domains).
