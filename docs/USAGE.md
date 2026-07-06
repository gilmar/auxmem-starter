# Usage

Full reference for the `auxmem` command. Run in place with `./auxmem-cli <cmd>` or install to get `auxmem <cmd>`.

## auxmem new

Creates a vault. Interactive when run bare; flag-driven when all of `--name`, `--path`, and at least one `--domain` are given.

### Interactive wizard
```bash
auxmem new
```
Prompts for a vault name (lowercase, hyphens), a path, and one or more domains. Domains are entered as `NN-folder=slug` (for example `10-projects=projects`), one per line, blank line to finish. A confirmation screen shows the plan before anything is written. The wizard requires a real terminal; in a pipe or CI it exits and tells you to use flags.

### Flag-driven (scriptable, CI-friendly)
```bash
auxmem new --name my-work --path ~/my-work \
  --domain 10-projects=projects \
  --domain 20-governance=governance \
  --domain 30-ops=ops
```
- `--name` lowercase letters, digits, hyphens.
- `--path` where to create it; must be empty or nonexistent.
- `--domain` repeatable; `NN-folder=slug`. Folder is `NN-lowercase-hyphen`, slug is lowercase/digits/hyphens. Order matters: the first domain becomes the "primary" used by the seed ADR and initial tasks.
- `--no-bootstrap` skip folder/hook/MOC/validate setup (rarely needed).

### What creation does
Copies the template, writes `.scripts/vault.config.json` from your inputs, substitutes the vault name and primary domain into seed content, then runs the vault's own `bootstrap.sh`: creates domain and structural folders, initializes git, installs the pre-commit hook, generates MOCs, and validates. A freshly created vault passes its own validator.

## auxmem seed

Stage 1 of seeding: normalize an AI provider export into a staging corpus outside any vault.
```bash
auxmem seed claude_conversations.json --staging ./seed-staging --since 2026-01-01
auxmem seed chatgpt_conversations.json --staging ./seed-staging
auxmem seed MyActivity.json --provider gemini --staging ./seed-staging --min-messages 3
```
- `--staging` where the corpus goes (outside the vault; default `./seed-staging`).
- `--provider` force the provider if auto-detection is wrong.
- `--since` skip conversations before this date.
- `--min-messages` drop trivial conversations.

Stage 2 (distillation into notes) is an agent step. Point your CLI agent at `importers/distill-seeds.md` and run it from the target vault. See `docs/IMPORTING.md`.

## auxmem import-obsidian

Import an existing Obsidian vault into an auxmem vault. Uses the obsidian-export pipeline by default, with a single-script fallback.
```bash
# rehearse first
auxmem import-obsidian ~/old-vault --dest ~/my-work --map map.json --dry-run
# real run
auxmem import-obsidian ~/old-vault --dest ~/my-work --map map.json
```
- `--dest` target auxmem vault (must already exist).
- `--map` folder-map JSON (old folder to new folder, plus optional exclude and default_domain).
- `--no-pipeline` use the single-script fallback instead of obsidian-export (no Rust toolchain needed).
- `--dry-run` show the move plan without writing.

The importer reads the target vault's config, so imported notes are validated against that vault's domains. It writes a migration report to the vault's `00-inbox/migration-report.md`; read it before committing. Unresolved links degrade to plain text, never broken links.

## auxmem doctor

Validate a vault and refresh its MOCs. Useful after manual edits or an import.
```bash
auxmem doctor ~/my-work
```
Runs the target vault's own `gen_mocs.py` then `validate_vault.py --all`.

## auxmem upgrade

Migrate an existing vault to the current template version. Safe to run anytime; it never touches your notes.
```bash
auxmem upgrade ~/my-work
auxmem upgrade ~/my-work --force   # re-apply even if already current
```

Each vault records the template version it was built from and keeps a pristine snapshot of managed files under `.auxmem/`. Upgrade compares that to the current template and applies a per-file policy:

- **Tooling** (validator, hook, gen_mocs, sync, bootstrap): replaced with the new version. Your copy is backed up first, and if you had edited it the report says so.
- **Config** (`vault.config.json`): structured merge. Your values (name, domains, and any scalar you set) are preserved; new schema keys and new vocabulary options are added. Reported line by line.
- **Guidance** (AGENTS.md, CLAUDE.md, GEMINI.md, README.md, docs, note templates): git 3-way merge against the snapshot. If you never edited a file, it updates cleanly. If you edited it and the template also changed it, you get either a clean merge or, where they truly collide, git conflict markers to resolve. Vaults created before versioning have no snapshot, so those files are preserved and the new version is written beside them as `<file>.new` for manual merging.
- **Content** (your notes, `72-tasks/todo.txt`, `72-tasks/done.txt`, decisions, MOCs): never touched. MOCs are regenerated at the end.

Everything replaced or merged is backed up under `.auxmem/backups/<timestamp>/` (git-ignored, local only) before any change. Upgrade then regenerates MOCs, runs the validator, and writes an `upgrade-report-*.md` into `00-inbox/` listing every change and anything needing your review. If validation fails after upgrade, the command warns and exits non-zero so you notice.

### Migrating task files to 72-tasks/ (template 1.1.0+)

Task files moved from the vault root into `72-tasks/`. Upgrade updates tooling and config but does not move your content. If your vault still has root-level task files:
```bash
mkdir -p 72-tasks
git mv todo.txt 72-tasks/todo.txt
[ -f done.txt ] && git mv done.txt 72-tasks/done.txt
./bootstrap.sh
```

### Cutting a new template version (maintainer)
1. Edit files under `template/`.
2. Bump `auxmem/version.py` (`TEMPLATE_VERSION`).
3. Run `python3 build_manifest.py` to regenerate `template/.auxmem-manifest.json`.
4. Commit. Vaults adopt the change on their next `auxmem upgrade`.

New files are classified automatically by path (`build_manifest.py` `policy_for`): `.scripts/` and `bootstrap.sh` are tooling, `vault.config.json` is merge, top-level guidance and `docs/*.md` and `90-templates/*.md` are 3-way, everything else is user content and stays unmanaged.

## Adding a domain to an existing vault

Domains live in the vault's `.scripts/vault.config.json`, not in the starter. To add one:
1. Edit that file's `domains` map.
2. Update any notes using removed slugs.
3. From the vault: `./bootstrap.sh` (creates the new folder) and `python3 .scripts/gen_mocs.py`.
4. `python3 .scripts/validate_vault.py --all`.
See the vault's `docs/SETUP.md` (Reconfiguring domains).
