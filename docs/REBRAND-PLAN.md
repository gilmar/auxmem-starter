# AuxMem rebrand plan

Product, marketing, and implementation plan for renaming **auxmem-starter** to **AuxMem**, introducing **AuxMem Manager** as the CLI product name, and replacing **vault** with **auxmem** as the name for a managed memory folder.

Status: implemented on branch `rebrand-auxmem`.

---

## Executive summary

AuxMem is moving from a “starter kit” framing to a product with a clear mental model:

| Layer | Name | What it is |
| --- | --- | --- |
| Project / brand | **AuxMem** | The open-source project, repo, and product identity |
| CLI tool | **AuxMem Manager** | The command-line tool that creates, validates, imports, and upgrades memory folders |
| Command | `auxmem` | How users invoke the manager (`auxmem new`, `auxmem doctor`, …) |
| Managed folder | **an auxmem** | A governed folder of plain-markdown memory (what we today call a “vault”) |

The Obsidian analogy is the anchor for discovery: *what a vault is to Obsidian, an auxmem is to AuxMem* — with the differentiator that an auxmem still works without any tooling installed.

This is a **2.0.0** release: breaking internal renames (config, validator, sync scripts) plus package and GitHub repo rename from `auxmem-starter` to `auxmem`. The timing is deliberate: neither name has ever been published to PyPI and the install base is small — a breaking rename is cheap now and becomes a migration project with every new adopter.

---

## Product and marketing review

### What works

**1. Three-level naming is coherent**

- **AuxMem** = brand (stable, capitalized, memorable).
- **AuxMem Manager** = the tool (clear job-to-be-done: manage auxmems).
- **auxmem** = the artifact users create and own (short, on-brand, matches the command).

This mirrors successful patterns: Docker (product) / `docker` (CLI) / container (thing); Obsidian (product) / app (tool) / vault (thing). Users learn one sentence and the rest follows.

**2. Dropping “starter” reduces positioning confusion**

“auxmem-starter” implied a bootstrap or template repo, not the product itself. Early adopters who installed via `uv tool install auxmem-starter` may have wondered whether they needed something else for production. **AuxMem** as the project name signals maturity.

**3. The Obsidian analogy is strong for the target audience**

People evaluating agent memory already know Obsidian vaults. “An auxmem” gives them an instant mental model without explaining YAML frontmatter first. Keep the analogy in the README hero and in one CLI help epilog line — not in every paragraph.

**4. “Manager” clarifies scope without overselling**

AuxMem is not a daemon, database, or SaaS. “Manager” correctly sets expectations: install once, run commands, folders stay yours. Avoid “platform,” “suite,” or “brain.”

### Risks and mitigations

| Risk | Severity | Mitigation |
| --- | --- | --- |
| **Homonym overload** — “auxmem” means brand, command, and folder | Medium | The anchor block is the real mitigation — repeat it verbatim in README, `--help` epilog, and wizard; capitalization rules and a README glossary support it but won’t carry it alone. Precedent that the pattern works: GitHub’s “gist” |
| **“Manager” feels enterprise-y** | Low | Pair with plain language: “the manager (`auxmem` command)”; never “AuxMem Manager Enterprise” |
| **Breaking 2.0 for existing users** | High | `auxmem upgrade` renames legacy files; CHANGELOG rename map; release notes with copy-paste migration steps |
| **GitHub/PyPI rename breaks links** | Medium | GitHub redirects old repo URLs, so git-URL installs keep working; neither name has ever been published to PyPI (both 404) — publish `auxmem` for the first time as part of 2.0 and reserve the name early |
| **Search/discovery** | Low | README first paragraph: “AuxMem (auxiliary memory)”; retain “auxiliary memory” once for SEO |
| **Plural awkwardness (“auxmems”)** | Low | Prefer “memory folders” or “your auxmem folders” in prose when plural sounds odd; use “auxmems” only in technical lists |

### Recommended messaging hierarchy

**One-liner (README, PyPI, GitHub description)**

> AuxMem — plain-markdown memory for AI agents, with a validation gate. No database, no lock-in: delete the tool and your notes are still just markdown and git.

Rule: hero copy uses plain words only — no coined terms before the anchor block has taught them. “Governed” and “an auxmem” earn their keep *after* the reader knows what they mean; “the manager creates auxmems you own” assumes vocabulary a first-time PyPI/GitHub visitor doesn’t have yet.

**Elevator (2 sentences)**

> AuxMem is auxiliary memory for AI agents: plain markdown, git, and a validation gate. Install the CLI (`auxmem`), create an auxmem, point your agent at it — the folder works even if you delete the tool.

**Do not say**

- “AuxMem vault” (pick auxmem *or* retire vault)
- “auxmem-starter” (retire entirely except CHANGELOG history)
- “The AuxMem Manager vault” (mixed metaphors)
- “AuxMem Manager” in running prose (allowed only in `--help`, PyPI description, and the README anchor block; elsewhere “the `auxmem` CLI”)

**Do say**

- “Create an auxmem with `auxmem new`”
- “Open your auxmem in …”
- “Upgrade your auxmem to template 2.0”
- “Import an Obsidian vault into your auxmem” (Obsidian keeps *vault*)

### Positioning vs competitors (unchanged thesis, clearer label)

The full comparison table lives in [docs/COMPARISONS.md](COMPARISONS.md) (the README links to it and uses “auxmem vault” in prose); rename “auxmem vault” to “an auxmem” in both. The bet remains: **files are the product**. The rebrand makes that easier to say in one breath.

### Release narrative (for CHANGELOG / GitHub release)

Title: **AuxMem 2.0 — product rename and auxmem terminology**

Bullets for users:

1. Project is now **AuxMem**; install with `uv tool install auxmem` — the first PyPI release (installs from the old git URL keep working via GitHub’s redirect).
2. CLI is the **AuxMem Manager**; command stays `auxmem`.
3. Your memory folders are **auxmems**, not vaults.
4. Run `auxmem upgrade <path>` then `./bootstrap.sh` in each existing folder to migrate file names and refresh the git hook; reinstall the sync timer if you use it (see Phase 3).

---

## Naming contract (canonical)

### Capitalization

| Term | Usage |
| --- | --- |
| **AuxMem** | Product, project, repo, images, README title |
| **AuxMem Manager** | `--help` title, PyPI description, and the README anchor block only — never in running prose; write “the `auxmem` CLI” instead. A label, not a brand: build no equity in “Manager” |
| `auxmem` | Shell command only |
| **an auxmem** / **your auxmem** | A managed folder |
| **auxmems** | Plural folders (sparingly; prefer “auxmem folders” in marketing copy) |
| **vault** | **Only** Obsidian vault (import source) |

### README anchor block (ship verbatim)

> **AuxMem** is the project. The **AuxMem Manager** (`auxmem` command) creates and maintains your memory folders. Each folder is an **auxmem** — what a vault is to Obsidian, an auxmem is to AuxMem, except the folder works without the app: delete the tooling and your notes are still just markdown and git.

### CLI help (top-level)

```
AuxMem Manager — create and maintain auxmems (governed markdown memory for AI agents).
Run from any directory; pass an auxmem path when a command needs an existing folder.
```

### pyproject.toml

```toml
name = "auxmem"
description = "AuxMem Manager: create and maintain provider-independent, agent-readable markdown memory (auxmems)."
```

---

## Implementation plan

### Phase 1 — Brand and prose (no breaking paths)

- [README.md](../README.md): title `# AuxMem`, anchor block, sweep vault → auxmem, retire auxmem-starter
- [docs/USAGE.md](USAGE.md), [docs/IMPORTING.md](IMPORTING.md), [docs/COMPARISONS.md](COMPARISONS.md): same terminology; keep “Obsidian vault” for import source
- [auxmem/cli.py](../auxmem/cli.py): description, epilog, subcommand help; metavars `VAULT` → `AUXMEM`
- [auxmem/wizard.py](../auxmem/wizard.py): wizard copy (“Name your auxmem”, etc.)
- [pyproject.toml](../pyproject.toml): package name and description
- [CHANGELOG.md](../CHANGELOG.md): 2.0.0 entry with rename map

### Phase 2 — Template internal renames (breaking)

Mechanical map:

| Old | New |
| --- | --- |
| `.scripts/vault.config.json` | `.scripts/auxmem.config.json` |
| `.scripts/validate_vault.py` | `.scripts/validate_auxmem.py` |
| `.scripts/vault-sync.sh` | `.scripts/auxmem-sync.sh` |
| `.scripts/vault-sync.systemd` | `.scripts/auxmem-sync.systemd` |
| `60-decisions/adr-0001-vault-structure.md` | `60-decisions/adr-0001-auxmem-structure.md` |
| Env `VAULT_AUTOSYNC` | `AUXMEM_AUTOSYNC` (accept legacy in hook for one release) |
| Default sync path `$HOME/vault` | `$HOME/auxmem` |

Update all references in: `bootstrap.sh`, `pre-commit`, Python scripts under `.scripts/`, [AGENTS.md](../auxmem/template/AGENTS.md), template docs, all `.skills/*/SKILL.md`, seed notes, templates. (Template `CLAUDE.md` is just an `@AGENTS.md` pointer — no change.)

Starter-side code: [scaffold.py](../auxmem/scaffold.py), [upgrade.py](../auxmem/upgrade.py), [importers.py](../auxmem/importers.py), [build_manifest.py](../build_manifest.py), [scripts/lint-shell.sh](../scripts/lint-shell.sh).

Importers (internal): `migrate_vault.py` → `migrate_obsidian.py`, `export_vault.sh` → `export_obsidian.sh`; rename `--vault-config` → `--auxmem-config` in **both** `migrate_obsidian.py` and `restructure_export.py` (it defines the same flag and `load_vault_domains`); sweep remaining vault prose in `seed_extract.py` and `distill-seeds.md`.

Versions: bump to **2.0.0** in all three places — CLI in [pyproject.toml](../pyproject.toml) (currently 1.2.1) **and** `auxmem/__init__.py` `__version__` (stale at 1.0.0 — fix the drift), template `TEMPLATE_VERSION` in [auxmem/version.py](../auxmem/version.py) (currently 1.3.1). Regenerate [`.auxmem-manifest.json`](../auxmem/template/.auxmem-manifest.json).

### Phase 3 — Upgrade migration

In [upgrade.py](../auxmem/upgrade.py), before manifest application:

1. Detect legacy layout (`vault.config.json` present, `auxmem.config.json` absent).
2. Rename files on disk and under `.auxmem/snapshot/`.
3. Rewrite old-manifest keys so overwrite/merge/merge3 policies match.
4. Report each rename in `00-inbox/upgrade-report-*.md`.
5. Document: run `./bootstrap.sh` after upgrade to refresh the git hook.
6. Installed sync timers break silently: the systemd unit users copied to `~/.config/systemd/user` has `ExecStart=%h/vault/.scripts/vault-sync.sh`, a path that stops existing after the rename. The upgrade report must tell users to reinstall the timer from the new `.scripts/auxmem-sync.systemd` — and note the default-path change (`$HOME/vault` → `$HOME/auxmem`): pass the folder path explicitly if it stays at `~/vault`.

Detectors `_vault()` → `_auxmem()` in **both** [upgrade.py](../auxmem/upgrade.py) and [importers.py](../auxmem/importers.py): accept either config filename, so imports into a not-yet-upgraded 1.x folder keep working (print a hint to run `auxmem upgrade`). `importers.py` also hardcodes `.scripts/vault.config.json` in two subprocess invocations — pass the detected filename instead.

### Phase 4 — Images

Generate and replace in [docs/images/](images/):

- `auxmem-banner.png` — **AuxMem** wordmark only (not “Manager” or “starter”)
- `auxmem-favicon.png` — square mark
- Remove unused `auxmem-logo-kit.png`

### Phase 5 — Repository rename

- `gh repo rename auxmem -R gilmar/auxmem-starter --yes`
- Update **both** remotes — `origin` and `upstream` point at the old name: `git remote set-url origin git@github.com:gilmar/auxmem.git`, then the same for `upstream` (or remove it)
- Publish `auxmem` **2.0.0** to PyPI (first release under either name; reserve the name early)
- Remove stale `auxmem_starter.egg-info/` and `build/` artifacts (`auxmem-cli` dev shim is unaffected — the package dir stays `auxmem`)

### Phase 6 — Verification

- [ ] `auxmem new` → fresh auxmem bootstraps; hook calls `validate_auxmem.py`
- [ ] Legacy folder from 1.x → `auxmem upgrade` renames files; validation passes after `./bootstrap.sh`; upgrade report includes the timer-reinstall note
- [ ] `bash scripts/lint-shell.sh` clean
- [ ] `rg -i vault` — hits only Obsidian import + CHANGELOG history
- [ ] `rg 'AuxMem Manager'` — hits only `cli.py` help, `pyproject.toml`, and the README anchor block
- [ ] `uv tool install .` installs `auxmem` command from package `auxmem`
- [ ] Versions agree at 2.0.0: `pyproject.toml`, `auxmem/__init__.py`, `auxmem/version.py`
- [ ] PR from branch `rebrand-auxmem`

---

## User-facing before / after

| Before | After |
| --- | --- |
| auxmem-starter | **AuxMem** (project) |
| the `auxmem` tool / CLI | **AuxMem Manager** (`auxmem` command) |
| create a vault | create **an auxmem** |
| `auxmem doctor ~/my-vault` | `auxmem doctor ~/my-work` (path unchanged; help text says auxmem) |
| `.scripts/vault.config.json` | `.scripts/auxmem.config.json` |
| `validate_vault.py` | `validate_auxmem.py` |
| import Obsidian **vault** | unchanged (Obsidian terminology) |

---

## Implementation todos

1. **Brand** — pyproject, README framing, version 2.0.0, CHANGELOG
2. **Template renames** — config, validator, sync scripts and all references
3. **Starter code** — scaffold, wizard, cli, upgrade, importers, build_manifest
4. **Migration** — legacy rename path in `auxmem upgrade`
5. **Prose sweep** — docs and skills; preserve Obsidian “vault”
6. **Images** — new banner and favicon
7. **Repo rename** — GitHub `auxmem`, update remote
8. **Verify** — fresh auxmem, legacy upgrade, lint, manifest, PR

---

## Open decisions (resolved)

| Question | Decision |
| --- | --- |
| Rename depth | Full rename including internal files + upgrade migration |
| Package / repo | Both → `auxmem` |
| Images | Generate new AuxMem-branded assets in implementation |
| CLI product name | **AuxMem Manager**; command stays `auxmem` |
| Project name | **AuxMem**; repo `gilmar/auxmem` |
| PyPI | Publish `auxmem` 2.0.0 as the first release (neither name was ever published) |
| Legacy config in importers | Accept either config filename, same as the upgrade detector; hint to run `auxmem upgrade` |
| Artifact noun (revisited 2026-07-11) | Considered `memdir` (maildir-style, distinct word — eliminates the homonym; namespace verified clean) and plain “memory folder”; **kept “an auxmem”** for category ownership of the noun. Gist precedent shows a product-noun homonym works when the anchor block does the teaching |
