<p align="center">
  <img src="docs/images/koinome-readme-banner.png" alt="Koinome — Knowledge in common. Governed corpora for humans and AI agents." width="100%">
</p>

Your AI agents forget everything. Koinome gives them — and you — a durable, governed memory made of plain Markdown files you own.

The unit is the **corpus**: a portable body of knowledge that lives as plain files on disk. The `koinome` CLI creates a corpus, keeps it healthy behind a deterministic validation gate, and equips any AI agent — Claude Code, Codex, Gemini CLI, Cursor — to read and maintain it, while you keep final say over every change. No accounts, no telemetry, no server.

## Why Koinome

AI agents are amnesiac. Every session starts from zero, so context, decisions, and durable facts evaporate between sessions, and you re-explain the same project, the same constraints, the same decisions, every time.

The memory products built to fix this share one shape: knowledge persists silently, in a provider's store, under a provider's account. You can't open it in an editor, diff it, or take it with you. And memory corruption compounds quietly — for work knowledge, decisions, and governance records, the rule is absolute: nothing rewrites authoritative knowledge while you sleep.

## How it works

The files are the product. Three commitments follow:

1. **Open standards only.** CommonMark, YAML frontmatter, git, and todo.txt. Any human or agent can read a corpus with no adapter.
2. **Governed, not free-form.** Deterministic validation and an optional git hook enforce the corpus contract. AI assists around the gate, never inside it.
3. **Authored, not compiled.** Derived synthesis pages cite sources and pass the same gate as authored notes.

Judge any memory system with the turn-it-off test: delete the tooling. With Koinome, delete every script and the corpus still works — notes open in any editor, git still diffs them, grep still finds them.

## Quick start

```bash
# run in place, no install
./koinome-cli new

# or install the command
pipx install .        # or: uv tool install .
koinome new           # or: koinome init (same scaffold today)
```

Interactive, or fully scriptable:

```bash
koinome new --name my-work --path ~/my-work
```

Or pass domains when the layout is already known:

```bash
koinome new --name my-work --path ~/my-work \
  --domain 10-projects=projects \
  --domain 20-governance=governance
```

This creates the corpus, installs the git hook, and sets up shared folders. Point your agent at it and run the `koinome-init` skill to finish setup. Requires Python 3.10+ and PyYAML.

## The full workflow

1. **Install** — `uv tool install .` or run `./koinome-cli`.
2. **Create a corpus** — `koinome new` or `koinome init` with `--name` and `--path`.
3. **Connect an agent** — open the corpus in Claude Code, Codex, Gemini CLI, or Cursor; run `koinome-init`.
4. **Author or import** — add notes, import exports with `koinome seed`, or distill seeds with `koinome-distill-seeds`.
5. **Validate** — `koinome doctor ~/my-corpus` or `python3 .scripts/validate_corpus.py --all` inside the corpus.
6. **Retrieve and synthesise** — use MOCs, grep, and `koinome-synthesize` for provenance-backed synthesis.
7. **Synchronise** — commit and push with git; optional `koinome_sync.py` for automated sync.
8. **Upgrade safely** — `koinome upgrade ~/my-corpus` refreshes managed tooling without touching your notes.
9. **Recover** — roll back from `.koinome/backups/` or git history; validation failures block bad commits.
10. **Remove tooling** — delete Koinome scripts; your Markdown and git history remain.

## Commands

| command | what it does |
| --- | --- |
| `koinome new` | Create a new corpus |
| `koinome init` | Same as `new` today (richer semantics planned) |
| `koinome seed` | Normalise a provider export to an import staging area |
| `koinome doctor CORPUS` | Validate a corpus and refresh navigation maps |
| `koinome check CORPUS` | Read-only conformance check (CI-safe) |
| `koinome upgrade CORPUS` | Upgrade Koinome-managed tooling without modifying user-authored knowledge |

See [docs/USAGE.md](docs/USAGE.md) for the full reference.

## Guarantees

1. **Every note opens as plain text** with no Koinome tooling installed.
2. **Validation is deterministic.** No model, no network, no server.
3. **AI assists around the gate, never inside it.** With every agent offline you can still read, write, validate, and commit.
4. **No Koinome process rewrites your notes unattended.** The optional scheduled job is git sync only.
5. **Derived pages cite their sources.** The validator rejects synthesis without provenance.
6. **Sensitive boundaries are physical.** Keep sensitive material in a separate private corpus on a path no agent reaches.
7. **No accounts, no telemetry.** Individual use is account-free, forever, and nothing phones home — not opt-out, not anonymised.
8. **Complete, free and open-source.** The individual corpus tooling is a complete local-first product, not a trial, a limited edition, or a funnel toward a hosted service.

## Where this is going

Sharing is the point. Koinome's thesis is that knowledge should move between people, teams, and organisations through explicit, governed operations — contributed, combined, merged, split, transferred, federated — with provenance and policy, not silent copies. Today's AI memory products can't represent that movement because they are single-principal by architecture: one owner, one boundary, one authority.

Today's release is deliberately the foundation for that thesis: a complete local-first product for **individual** corpora, one corpus at a time. Cross-corpus operations are design scope and proceed through public RFCs — they are **not** shipped software, and this project never blurs the two.

The full plan — the single-principal claim in full, the operation lifecycle, the roadmap, and the commitments that bind the project — is in **[docs/STRATEGY.md](docs/STRATEGY.md)**.

## Licence

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE). Contributions are accepted under the [Developer Certificate of Origin](https://developercertificate.org/); there is no CLA. See [CONTRIBUTING.md](CONTRIBUTING.md).
