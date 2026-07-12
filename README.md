<p align="center">
  <img src="docs/images/koinome-readme-banner.png" alt="Koinome — Knowledge in common. Governed corpora for humans and AI agents." width="100%">
</p>

Koinome is a governed knowledge system for humans and AI agents. Its unit is the **corpus**: a portable, governed body of knowledge belonging to a person, agent, project, team, community, or organisation. The `koinome` CLI creates and maintains corpora as plain Markdown on disk, with a deterministic validation gate.

Sharing is the point: knowledge should be contributed, combined, merged, split, transferred, and federated across boundaries—with provenance and policy, not silent copies. Today's release is the foundation for that thesis: a complete **local-first** product for **individual** corpora ([strategy D1](docs/STRATEGY.md)). Read the full strategy in **[docs/STRATEGY.md](docs/STRATEGY.md)**.

## Current scope

The current Koinome release manages individual corpora, **one corpus at a time**. **Cross-corpus** operations (share, contribute, transfer, merge, split, combine, federate, and the rest) are design scope and proceed via public RFCs—they are **not** shipped software.

## Commitments

These match [strategy §5](docs/STRATEGY.md):

- **Local-first.** A corpus is a directory of plain files. It works offline without Koinome running.
- **Individual use is account-free, forever.** No sign-up, login, or hosted dependency for local use.
- **No telemetry.** Not opt-out, not anonymised.
- **Human-approved persistence.** Nothing becomes canonical without deterministic validation and explicit approval.
- **Nothing crosses a boundary silently.** Every movement between corpora is an approved operation that leaves a receipt (design scope until operations ship).
- **The AI proposes; it never decides.**
- **Complete and free.** Individual corpus tooling is and will remain complete, free, and open-source—not a trial or funnel.
- **Portable by construction.** CommonMark and YAML remain useful if Koinome is deleted tomorrow.

## The claim

Koinome argues that today's AI memory products are **single-principal by architecture**—one owner, one boundary—not a missing feature. The essay and checkable claim are in [strategy §3](docs/STRATEGY.md).

## Free and open-source commitment

Koinome for individual use is a complete local-first product, not a limited edition of a hosted service. The individual corpus format, local tooling, validation, agent workflows, imports, exports, synthesis, migration, synchronisation, backup, and recovery are **free and open-source** and are intended to remain so.

You can create, maintain, and use local corpora without a Koinome account, subscription, or hosted service.

## The problem

AI agents are amnesiac. Every session starts from zero, so context, decisions, and durable facts evaporate between sessions.

Judge any fix with the turn-it-off test: delete the tooling. With Koinome, delete every script and the corpus still works — notes open in any editor, git still diffs them, grep still finds them.

Memory corruption compounds quietly. For work knowledge, decisions, and governance records, the rule is absolute: nothing rewrites authoritative knowledge while you sleep.

## The idea

The files are the product. Three commitments follow:

1. **Open standards only.** CommonMark, YAML frontmatter, git, and todo.txt. Any human or agent can read a corpus with no adapter.
2. **Governed, not free-form.** Deterministic validation and an optional git hook enforce the corpus contract. AI assists around the gate, never inside it.
3. **Authored, not compiled.** Derived synthesis pages cite sources and pass the same gate as authored notes.

## Guarantees

1. **Every note opens as plain text** with no Koinome tooling installed.
2. **Validation is deterministic.** No model, no network, no server.
3. **AI assists around the gate, never inside it.** With every agent offline you can still read, write, validate, and commit.
4. **No Koinome process rewrites your notes unattended.** The optional scheduled job is git sync only.
5. **Derived pages cite their sources.** The validator rejects synthesis without provenance.
6. **Sensitive boundaries are physical.** Keep sensitive material in a separate private corpus on a path no agent reaches.

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
# equivalent: koinome init --name my-work --path ~/my-work
```

Or pass domains when the layout is already known:

```bash
koinome new --name my-work --path ~/my-work \
  --domain 10-projects=projects \
  --domain 20-governance=governance
```

This creates the corpus, installs the git hook, and sets up shared folders. Point your agent at it and run the `koinome-init` skill to finish setup. Requires Python 3.10+ and PyYAML.

## End-to-end individual workflow

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
| `koinome init` | Same as `new` today (strategy demo name; richer semantics planned) |
| `koinome seed` | Normalise a provider export to an import staging area |
| `koinome doctor CORPUS` | Validate a corpus and refresh navigation maps |
| `koinome check CORPUS` | Read-only conformance check (CI-safe) |
| `koinome upgrade CORPUS` | Upgrade Koinome-managed tooling without modifying user-authored knowledge |

See [docs/USAGE.md](docs/USAGE.md) for full reference.

## Licence

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE). Contributions are accepted under the [Developer Certificate of Origin](https://developercertificate.org/); there is no CLA. See [CONTRIBUTING.md](CONTRIBUTING.md).
