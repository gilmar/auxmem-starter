# Transform AuxMem into Koinome

You are working in the repository:

`https://github.com/gilmar/auxmem`

Transform the existing AuxMem project into **Koinome**.

This is a complete product, package, CLI, template, documentation, test, example, and on-disk-format migration—not a superficial search-and-replace.

Execute the transformation fully. Do not stop after producing a plan. Do not push, publish a package, rename the GitHub repository, or expose private strategy documents unless explicitly instructed.

## Product model

Use the following terminology consistently.

### Koinome

**Koinome** is the product and system that creates and manages knowledge corpora.

Use:

- `Koinome` in prose and headings.
- `koinome` for packages, commands, paths, filenames, and technical identifiers.

Koinome should no longer be described primarily as “auxiliary memory”. Its broader purpose is durable, governed knowledge that can be used by a person and their AI agents.

### Corpus

A **corpus** is the unit currently created and managed by Koinome.

Use this definition:

> A corpus is a portable, governed body of knowledge maintained by an individual and usable by that individual and their authorised AI agents.

The plural is **corpora**, never “corpuses”.

Examples:

- Create a corpus.
- Validate the corpus.
- Import notes into a corpus.
- Upgrade an existing corpus.
- Point an AI agent at the corpus.
- Keep sensitive material in a separate private corpus.
- Koinome currently manages one corpus at a time.

Do not call an individual corpus:

- a Koinome;
- an auxmem;
- a workspace;
- a space;
- a base;
- a vault;
- a repository;
- a memory folder;
- a knowledge base.

A corpus may be stored in a Git repository, but the corpus and the repository are not the same concept.

## Current product scope

The current implementation is for **individual use**.

It creates and maintains independently governed corpora for a person and their AI agents. A person may have more than one corpus—for example, personal, work, or project corpora—but Koinome does not yet operate across them.

Do not implement:

- corpus sharing;
- partial corpus sharing;
- corpus transfer;
- corpus combination;
- corpus merging;
- corpus federation;
- cross-corpus permissions;
- organisational accounts;
- team collaboration;
- hosted coordination;
- policy negotiation between corpora;
- enterprise administration.

Do not add placeholder commands for these operations.

In the future, operations such as sharing, transferring, combining, or merging corpora will be **semantic, policy-aware, and AI-mediated**. They must not be modelled as mechanical Git merges, directory copies, or file concatenation.

Therefore:

- Do not create mechanical `merge`, `share`, `transfer`, or `combine` commands.
- Do not describe Git merge as corpus merging.
- Do not introduce APIs that assume future cross-corpus operations are file-level operations.
- Keep Git as an implementation mechanism for storage, history, synchronisation, and rollback within an individual corpus.
- A three-way file merge used during template upgrade remains an implementation detail and must not be described as a corpus merge.

Public documentation may state that cross-corpus operations are outside the current scope. Do not publish the confidential long-term Koinome strategy, enterprise plans, or detailed future architecture.

## Permanent free and open-source individual product

The individual-use corpus is the foundation of Koinome and must be genuinely useful on its own today.

It is not:

- a prototype for a future commercial product;
- a limited community edition;
- a trial version;
- a thin client for a future hosted service;
- a deliberately incomplete version intended to drive upgrades;
- disposable scaffolding for future team or enterprise functionality.

Koinome for individual use—including its local corpus format, tooling, and workflows—is and will remain **free and open-source**.

The current repository is MIT-licensed. Preserve the MIT licence in `LICENSE`, package metadata, generated templates, and public documentation unless the user explicitly makes a separate licensing decision. Do not replace it with a source-available licence, restrict individual use, or introduce licensing terms that contradict the permanent free/open-source commitment.

A person must be able to create, maintain, and use one or more local corpora indefinitely without:

- creating an online account;
- connecting to a Koinome-hosted service;
- paying a subscription;
- using a proprietary model provider;
- storing canonical knowledge in a database;
- depending on a proprietary canonical index;
- granting Koinome access to corpus contents;
- accepting vendor lock-in.

The transformation from AuxMem to Koinome must preserve and improve the immediate usefulness of the current product.

A completed individual corpus must support the existing practical workflows:

- creating a corpus;
- configuring its knowledge domains;
- authoring and organising durable records;
- using the corpus with different coding and AI agents;
- validating proposed changes deterministically;
- importing existing knowledge;
- distilling AI conversation exports;
- maintaining decisions and tasks;
- producing provenance-backed synthesis;
- detecting stale derived material;
- generating navigation and graph reports;
- synchronising the corpus through Git;
- upgrading Koinome-managed tooling safely;
- backing up and recovering a corpus;
- recovering from errors without losing user-authored knowledge;
- operating completely offline except where the user independently chooses to invoke an AI model or Git remote.

Do not remove or weaken an existing individual-use capability merely because it may later overlap with a hosted or organisational product.

Do not introduce artificial open-core boundaries into individual use. In particular, do not reserve the following for a future paid edition:

- deterministic validation;
- schema configuration;
- provenance enforcement;
- synthesis workflows;
- local agent integrations;
- imports and exports;
- local indexing or search;
- Git synchronisation;
- backup and recovery;
- migration tooling;
- corpus health checks;
- local policy enforcement;
- support for multiple local corpora owned by the same person.

Future commercial value may come from capabilities whose complexity is inherently collective or operational, such as:

- organisational identity and access management;
- managed sharing between independently governed corpora;
- semantic transfer and combination across corpus boundaries;
- policy negotiation and approval workflows;
- audit and compliance infrastructure;
- hosted coordination and administration;
- managed cross-corpus discovery and indexing;
- employee and contributor lifecycle workflows;
- enterprise integrations, deployment, and support.

Those future capabilities must extend the free and open-source individual product rather than make it dependent on them.

The product boundary is:

> **Commercial Koinome extends the individual corpus; it does not complete, unlock, or replace it.**

### Product quality requirement

Treat the renamed Koinome release as a usable product release, not a branding checkpoint.

The repository should leave an individual user able to:

1. Install Koinome.
2. Create a corpus.
3. Understand the corpus model from the documentation.
4. Connect a supported AI coding agent.
5. Import or author useful knowledge.
6. Validate and commit that knowledge.
7. Retrieve and synthesise it in later sessions.
8. Synchronise and recover the corpus.
9. Upgrade the managed tooling without losing their work.
10. Remove Koinome tooling and retain readable Markdown and Git history.

Documentation must include a coherent end-to-end individual workflow demonstrating these steps.

The README should communicate both commitments clearly:

> Koinome currently provides a complete local-first corpus for individual use.

> The individual corpus and its local tooling are free and open-source and are intended to remain so.

## Preserve the existing architectural principles

Preserve the substantive behaviour and guarantees already implemented in AuxMem:

- Plain Markdown and YAML frontmatter remain canonical.
- Git remains optional infrastructure for history, synchronisation, and recovery.
- The files remain usable when Koinome is removed.
- Validation remains deterministic and model-independent.
- AI assistance remains outside the deterministic validation gate.
- Agents may draft, restructure, synthesise, and propose corrections.
- Nothing silently rewrites authoritative knowledge.
- Derived documents must retain provenance.
- Sensitive data boundaries remain physical rather than frontmatter-based.
- Configuration remains the single source of truth.
- Managed-template upgrades remain transactional.
- User-authored notes are never silently modified by upgrades.
- Existing import, validation, MOC, synthesis, graph, sync, and evaluation behaviour must continue working.

This task is a product, ontology, and usability transformation. Preserve the proven architecture, but fix naming, documentation, or workflow problems that prevent the individual corpus from being coherent and useful as Koinome today. Avoid speculative infrastructure for future organisational features.

## Canonical naming rules

Apply the following distinction:

- Product-owned tooling and metadata use **Koinome**.
- The managed knowledge object is a **corpus**.

Use these target names unless an existing technical constraint makes one impossible:

| Current | Target |
|---|---|
| `AuxMem` | `Koinome` |
| `auxmem` command | `koinome` |
| `auxmem` Python package | `koinome` |
| `auxmem-cli` | `koinome-cli` |
| `auxmem/template` | `koinome/template` |
| “an auxmem” | “a corpus” |
| “auxmems” | “corpora” |
| “AuxMem Manager” | “Koinome CLI” or “Koinome” |
| `.auxmem/` | `.koinome/` |
| `.auxmem-manifest.json` | `.koinome-manifest.json` |
| `.scripts/auxmem.config.json` | `.scripts/koinome.config.json` |
| `.scripts/validate_auxmem.py` | `.scripts/validate_corpus.py` |
| `.scripts/check_auxmem.py` | `.scripts/check_corpus.py` |
| `.scripts/auxmem_sync.py` | `.scripts/koinome_sync.py` |
| `.scripts/auxmem-sync.sh` | `.scripts/koinome-sync.sh` |
| `.scripts/auxmem-sync.systemd` | an appropriately named Koinome systemd unit |
| `.skills/auxmem-*` | `.skills/koinome-*` |
| `adr-0001-auxmem-structure.md` | `adr-0001-corpus-structure.md` |
| `__AUXMEM_NAME__` | `__CORPUS_NAME__` |
| `AuxmemPathError` | `CorpusPathError` |
| `resolve_auxmem` | `resolve_corpus` |
| `scaffold_auxmem` | `scaffold_corpus` |

Follow this naming rule in functions, types, variables, and messages:

- Prefer `corpus`, `corpus_path`, `source_corpus`, and `target_corpus` for domain objects.
- Prefer `koinome` for product-owned implementation, configuration, state, and tooling.
- Avoid identifiers such as `koinome_path` when the value is actually the path to a corpus.

Do not blindly replace the substring `auxmem`. Inspect each occurrence semantically.

## CLI

Rename the executable to:

```bash
koinome
```

Keep the existing simple command topology:

```bash
koinome new
koinome seed
koinome doctor
koinome check
koinome upgrade
```

Do not introduce a redundant `koinome corpus ...` namespace at this stage.

Update all CLI help, descriptions, epilogues, examples, errors, and metavariables.

Examples of expected language:

```text
koinome new
    Create a new corpus.

koinome check CORPUS
    Perform a read-only conformance check on a corpus.

koinome doctor CORPUS
    Validate a corpus and refresh its generated navigation.

koinome upgrade CORPUS
    Upgrade Koinome-managed tooling without modifying user-authored knowledge.
```

A successful creation should say something similar to:

```text
Created corpus at /path/to/corpus.
Next: point your agent at the corpus and run the koinome-init skill.
```

Reserve the word **corpus** for a Koinome-managed knowledge collection.

The current `seed` command refers to its intermediate output as a “staging corpus”. Rename that concept to something such as:

- staging area;
- import staging area;
- normalised export;
- staging dataset.

It is not yet a Koinome corpus.

## Python package and distribution

Rename the Python package and distribution comprehensively:

- `auxmem/` → `koinome/`
- project name in `pyproject.toml` → `koinome`
- console script → `koinome = "koinome.cli:main"`
- package-data paths
- internal imports
- test imports
- module docstrings
- wrapper scripts
- build-manifest tooling
- release documentation
- installation instructions
- references in CI workflows

Ensure the package still includes hidden template files, skills, scripts, workflows, manifests, and importer assets.

Do not publish to PyPI or any other registry.

Report package or registry names that require manual availability checks.

## On-disk Koinome state

New corpora must use Koinome-branded managed state.

The intended shape is:

```text
my-corpus/
├── .koinome/
│   ├── manifest.json
│   ├── snapshot/
│   └── backups/
├── .scripts/
│   ├── koinome.config.json
│   ├── validate_corpus.py
│   ├── check_corpus.py
│   ├── koinome_sync.py
│   └── ...
├── .skills/
│   ├── koinome-init/
│   ├── koinome-new-note/
│   ├── koinome-synthesize/
│   └── ...
├── AGENTS.md
└── ...
```

Keep the current shallow knowledge structure and existing structural folders unless a rename is necessary for product terminology.

Update:

- package manifests;
- generated snapshots;
- bootstrap scripts;
- pre-commit hooks;
- CI workflows installed in corpora;
- systemd files;
- config readers;
- validators;
- importers;
- MOC generators;
- synthesis tooling;
- graph tooling;
- sync tooling;
- upgrade tooling;
- examples;
- evaluation fixtures.

There must be one canonical Koinome configuration path. Do not leave multiple active configuration names.

## Legacy AuxMem migration

Existing AuxMem folders must have a safe path to become Koinome corpora.

Implement legacy layout detection in `koinome upgrade PATH`.

It must recognise at least:

- `.auxmem/manifest.json`;
- `.auxmem/snapshot/`;
- `.auxmem/backups/`;
- `.scripts/auxmem.config.json`;
- AuxMem-named managed scripts;
- AuxMem-prefixed skills;
- the AuxMem structural ADR;
- existing manifest entries containing AuxMem paths.

The migration must:

1. Detect that the target is a legacy AuxMem folder.
2. Build an inspectable migration plan.
3. Support `--dry-run`.
4. Back up every managed file affected.
5. Rename product-owned managed state to Koinome names.
6. Remap manifest and snapshot paths.
7. Preserve user configuration values.
8. Preserve user modifications to managed guidance using the existing merge policy.
9. Never rewrite ordinary user-authored notes automatically.
10. Refresh generated navigation where appropriate.
11. Run post-migration validation.
12. Roll back the managed state if a required post-check fails.
13. Produce a migration report.
14. Leave the corpus in one coherent format rather than a permanent mixture of AuxMem and Koinome names.

When user-authored notes contain links or commands using old AuxMem names, report those references for manual review rather than silently editing the notes.

Do not retain the old `auxmem` command as a first-class product command merely for compatibility. The migration entry point is the new `koinome upgrade`.

Legacy names may remain only in:

- migration detection;
- legacy fixtures;
- migration tests;
- a concise migration guide;
- a changelog or historical note.

Keep legacy compatibility isolated. Do not allow it to contaminate normal new-corpus code paths.

## Documentation and public positioning

Rewrite the README and documentation around the new product model.

A suitable opening definition is:

> **Koinome is a local-first, plain-Markdown system for creating and maintaining a personal knowledge corpus for a person and their AI agents, with a deterministic validation gate.**

Then define:

> A **corpus** is a portable, governed body of knowledge maintained by an individual and usable by that individual and their authorised AI agents.

Clearly distinguish:

- **Koinome** — the product and tooling;
- **corpus** — the governed knowledge collection;
- **record or note** — an individual knowledge item;
- **Git repository** — an optional storage and history mechanism;
- **staging area** — temporary import material that has not entered a corpus.

Add a concise **Current scope** section:

> The current Koinome release manages individual corpora, one corpus at a time. Cross-corpus sharing, transfer, combination, and federation are not implemented.

Add a concise **Free and open-source commitment** section:

> Koinome for individual use is a complete local-first product, not a limited edition of a hosted service. The individual corpus format, local tooling, validation, agent workflows, imports, exports, search, synthesis, migration, synchronisation, backup, and recovery are free and open-source and are intended to remain so.

Do not describe future corpus operations as file copying or Git merging.

Replace phrases such as:

- “plain-markdown memory”;
- “memory folder”;
- “an auxmem”;
- “AuxMem Manager”;
- “personal-to-team-scale”;
- “staging corpus”, where it means temporary import material.

Use “memory” only when discussing the specific problem of AI session memory. Do not make it the product category.

Update:

- README;
- usage documentation;
- architecture documentation;
- importing documentation;
- fixing and conflict documentation;
- synthesis documentation;
- comparison tables;
- evaluation documentation;
- compatibility and release documentation;
- template README and AGENTS instructions;
- skill contents and frontmatter;
- examples and their notes;
- ADRs;
- command examples;
- source comments and docstrings.

Do not add a private `STRATEGY.md` or disclose confidential commercial strategy.

The current AuxMem banner is obsolete. Remove the AuxMem-branded banner or replace it with a neutral text-only presentation. Do not invent or generate a Koinome logo.

## Architecture wording

Preserve the existing admission-plane and enforcement-plane distinction.

Use wording such as:

> AI may help a person author, organise, synthesise, and repair knowledge in a corpus. Deterministic tooling decides whether a proposed change satisfies the corpus contract.

Do not imply that deterministic validation verifies truth.

Preserve the rule:

> AI assists around the gate, never inside it.

Clarify that this rule concerns operations inside the current individual corpus. It does not define the eventual semantics of AI-mediated operations between corpora.

Where the architecture discusses sync and upgrade:

- describe Git merges as file- or template-level conflict handling;
- never call them corpus merging;
- distinguish synchronising replicas of one corpus from combining two independent corpora.

## Skills

Rename all skill directories and skill frontmatter from `auxmem-*` to `koinome-*`.

Examples:

- `koinome-init`
- `koinome-setup-domains`
- `koinome-new-note`
- `koinome-adr`
- `koinome-todo`
- `koinome-synthesize`
- `koinome-session-close`
- `koinome-distill-seeds`

Update every cross-reference, bootstrap link, and provider-specific installation path.

Keep the skills provider-independent and based on the existing plain `SKILL.md` format.

## Examples and evaluation fixtures

The existing examples should become examples of Koinome corpora.

Use language such as:

- reference corpus;
- research corpus;
- software-project corpus;
- consulting-engagement corpus.

Update all copied managed state inside examples, including hidden snapshots and manifests.

Do not manually change only the visible files while leaving snapshots stale. Regenerate or systematically update fixtures so they represent exactly what a newly scaffolded corpus would contain.

Ensure evaluation and conformance tooling compares against Koinome corpora rather than AuxMem folders.

At least one example must demonstrate the complete individual workflow from corpus creation through agent-assisted authoring, validation, retrieval, synthesis, synchronisation, safe upgrade, and recovery.

## Tests

Update the complete test suite, including tests covering:

- CLI smoke behaviour;
- scaffolding;
- validator behaviour;
- package data;
- bootstrap;
- sync;
- imports;
- staged snapshots;
- upgrade transactions;
- exit codes;
- documentation consistency;
- reference evaluations.

Add dedicated tests for:

1. Creating a fresh Koinome corpus.
2. Detecting a legacy AuxMem folder.
3. Dry-running an AuxMem-to-Koinome migration.
4. Successfully migrating an unmodified legacy corpus.
5. Preserving user-edited managed guidance.
6. Preserving ordinary user notes byte-for-byte.
7. Rolling back after a failed post-migration check.
8. Remapping manifest and snapshot paths.
9. Reporting legacy references found in user-authored notes.
10. Ensuring a new corpus contains no active AuxMem-branded paths.
11. Ensuring `koinome check`, `doctor`, and `upgrade` accept corpus paths.
12. Ensuring documentation uses `corpus` and `corpora` correctly.
13. Completing the individual end-to-end workflow without a Koinome account or hosted service.
14. Operating core local commands with network access unavailable.
15. Verifying that no essential individual feature is gated behind a paid or hosted component.
16. Removing Koinome-managed tooling while preserving readable user-authored Markdown and Git history.

Create a repository-wide consistency test that searches for obsolete names.

After the migration work, a case-insensitive search for:

```text
auxmem
AuxMem
auxiliary memory
an auxmem
auxmems
```

must return only explicitly allowlisted legacy-migration or historical references.

Keep that allowlist narrow and documented.

## Verification

Run all appropriate checks, including:

```bash
pytest
ruff check .
python -m build
```

Also perform these smoke tests in temporary directories:

```bash
koinome --help
koinome new --name test-corpus --path /tmp/test-corpus
koinome check /tmp/test-corpus
koinome doctor /tmp/test-corpus
koinome upgrade --dry-run /tmp/test-corpus
```

Install the built package into an isolated environment and verify that:

- the `koinome` executable is installed;
- no `auxmem` executable is installed;
- all template package data is present;
- hidden managed files are included;
- a scaffolded corpus validates;
- agent skills and bootstrap links work;
- the Git hook invokes the renamed validator;
- examples pass the evaluation harness;
- ordinary individual workflows require no Koinome account, subscription, or hosted service;
- the core workflow remains usable with networking disabled, except for independently chosen AI-provider or Git-remote calls.

Create a representative legacy AuxMem fixture and verify the full migration path.

## Completion criteria

The work is complete only when:

- The Python package is `koinome`.
- The CLI command is `koinome`.
- The product is called Koinome throughout active code and documentation.
- The managed object is consistently called a corpus.
- The plural is consistently corpora.
- New corpora use `.koinome` managed state.
- Existing AuxMem folders can be transactionally migrated.
- User-authored notes are preserved.
- Existing behaviour remains operational.
- Tests, linting, packaging, and smoke checks pass.
- Examples and snapshots are internally consistent.
- No future sharing or merging functionality has been implemented.
- Git operations are not presented as semantic corpus operations.
- No confidential strategy has been added to the public repository.
- No obsolete AuxMem branding remains outside tightly scoped legacy compatibility.
- The individual corpus remains a complete and immediately useful product.
- Existing individual-use workflows have not been lost during the transformation.
- No Koinome account, hosted service, subscription, or paid component is required for ordinary individual use.
- Core local capabilities are not artificially restricted in anticipation of commercial offerings.
- Public documentation states that individual Koinome corpora and their local tooling are permanently free and open-source.
- The current MIT licence is preserved consistently across the repository and packaged artifacts.
- At least one tested end-to-end workflow demonstrates installation, corpus creation, agent use, import or authoring, validation, retrieval, synthesis, synchronisation, recovery, and safe upgrade.
- Removing Koinome tooling leaves the user with readable, portable knowledge and usable history.

## Final response

At completion, report:

1. The main naming and structural changes.
2. The legacy migration behaviour.
3. The complete individual workflow that was preserved or improved.
4. How the permanent free/open-source boundary is represented in code and documentation.
5. Any behaviour deliberately left unchanged.
6. Every test and verification command run.
7. Any failures or limitations.
8. Manual actions still required, such as:
   - renaming the GitHub repository;
   - updating repository settings and URLs;
   - checking package-registry availability;
   - configuring domains;
   - replacing visual branding later.

Do not claim success for checks that were not actually run.
