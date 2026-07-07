![auxmem banner](docs/images/auxmem-banner.png)

# auxmem-starter

**Memory for AI agents, in plain markdown you own. Works with any model, survives any vendor switch, and nothing rewrites it behind your back.**

The bet: for governed work memory, **the files are the product, not an index of the product**. An *auxmem vault* is a knowledge base made of nothing but markdown, YAML frontmatter, git, and todo.txt. No database, no SaaS, no plugins. You and your AI agents (Claude Code, Codex, Gemini CLI) both read and write it, and it stays yours across every model and vendor change that comes later.

*auxmem* is short for *auxiliary memory*, and it names the vault standard. **auxmem-starter** is this project: the `auxmem` tool that stands a vault up, installs its git hook and validator, and keeps it healthy across template versions. A vault is not a brain. It is the durable state your agents write to and read from. Capture and reasoning happen in whatever tools you already use. The vault holds what must persist.

---

## The problem

AI agents are amnesiac. Every session starts from zero, so the context you built up yesterday, the decisions you made, the people and systems you track, all of it evaporates.

Judge any fix with the turn-it-off test: delete the tooling and see what is left. Delete every piece of auxmem tooling and the memory still works. Notes open in any editor, git still diffs them, grep still finds them. The common fixes fail the test:

- **Provider memory** fails the day you switch vendors. Your context sits on their servers, in their format. You cannot read it, grep it, or move it.
- **A vector database or "second brain" SaaS** fails with its server and its embedding model. Your notes become an opaque index you no longer own.
- **An agent freely maintaining your knowledge base** fails silently. It rewrites a fact, drifts a summary across edits, quietly corrupts the one note you needed to trust.

Worst case with auxmem, you are holding a folder of readable text.

And memory corruption compounds. Wrong code fails loudly, in a test or a stack trace. A wrong note does not crash anything: it gets read, trusted, cited, and folded into later synthesis, and by the time you notice, you cannot say when it went wrong. For personal research, some drift is fine. For work memory, decisions, governance records, stakeholder state, it is a liability. So the rule is absolute: nothing rewrites your knowledge while you sleep.

## The idea

The files are the product. Three commitments follow from that bet:

1. **Open standards only.** Everything is CommonMark, YAML frontmatter, git, and todo.txt. Any human can edit a vault in any editor. Any agent can read it with no adapter. It will still open in ten years with no server running.
2. **Governed, not free-form.** A validator and a git hook enforce a frontmatter and structure contract. Metadata stays clean and greppable because it has to. The gate is what lets you and your agents write loosely and still end up with a trustworthy record. Reading is never gated, writing always is: retrieval is plain grep and glob, and nothing enters the record without passing the hook.
3. **Authored, not compiled.** A note enters the record under human accountability. Authoring is *AI-assisted by default and manual when you want*, but synthesis into derived pages is an explicit, provenance-checked step, never a silent runtime process.

"Authored" means accountable, not hand-typed. An agent can draft, restructure, and file a note. You author it in the sense that it is your record and your responsibility. When validation fails, the tooling helps fix it: mechanical errors auto-repair with no model, judgment errors get an agent-drafted fix you accept, and genuinely ambiguous ones ask you. The gate never weakens; the typing stays light.

## Quick start

```bash
# run in place, no install
./auxmem-cli new

# or install the command
pipx install .        # or: uv tool install .
auxmem new
```

Interactive, or fully scriptable:

```bash
auxmem new --name my-work --path ~/my-work \
  --domain 10-projects=projects \
  --domain 20-governance=governance \
  --domain 30-ops=ops
```

This creates the vault, installs the git hook, generates navigation, and validates. Then point your agent at it and start working. Requires Python 3.10+ and PyYAML. On WSL2, keep vaults on the Linux filesystem.

## Commands

| command | what it does |
|---|---|
| `auxmem new` | create a vault (interactive wizard, or `--name/--path/--domain`) |
| `auxmem seed EXPORT.json` | normalize a Claude, ChatGPT, or Gemini export into a staging corpus |
| `auxmem import-obsidian SRC --dest VAULT` | import an existing Obsidian vault |
| `auxmem doctor VAULT` | validate a vault and refresh its navigation |
| `auxmem upgrade VAULT` | migrate a vault to the current template version, safely |

See [`docs/USAGE.md`](docs/USAGE.md) for the full reference and [`docs/IMPORTING.md`](docs/IMPORTING.md) for seeding and migration.

## What a vault contains

A shallow, stable folder layout optimized for how agents actually retrieve: filesystem and lexical search over descriptive filenames and frontmatter, not vector similarity.

```
my-work/
├── AGENTS.md          agent guide; CLAUDE.md and GEMINI.md point here
├── 00-inbox/          unsorted captures
├── 05-sources/        raw immutable intake, the synthesis queue
├── 10-projects/       your authored domains (10-50, named in your config)
├── 20-governance/
├── 60-decisions/      ADR log, append-only
├── 70-meetings/
├── 71-log/            dated session logs
├── 72-tasks/          todo.txt and done.txt
├── 80-moc/            generated maps of content
├── 85-synthesis/      derived pages, provenance enforced
├── 90-templates/      note templates
├── .skills/           agent workflows (session close, synthesis, fixes)
└── .scripts/          validator, hook, generators, one config file
```

Every note is plain markdown under a frontmatter contract. A real one:

```markdown
---
title: ADR-0002 Postgres over DynamoDB for the billing store
summary: Billing needs transactional integrity across invoice and ledger writes. Postgres wins over DynamoDB despite the operations cost.
type: adr
status: active
domain: projects
created: 2026-07-06
updated: 2026-07-06
tags: [billing, database]
---
## Decision
Use Postgres. Invoice and ledger writes must commit atomically, and the team already operates it in two services.
```

The contract is enforced when a note enters the record:

```
$ python3 .scripts/validate_vault.py 20-governance/access-review.md
20-governance/access-review.md
  - missing required field: updated  [auto]
  - use plural 'tags' with list syntax, not 'tag'  [auto]
2 item(s) are auto-fixable: run  python3 .scripts/validate_vault.py --fix --all

$ python3 .scripts/validate_vault.py --fix 20-governance/access-review.md
auto-fixed 2 item(s):
  20-governance/access-review.md: renamed 'tag' to 'tags'
  20-governance/access-review.md: set missing 'updated' to today
vault validation clean.
```

Every vault carries its own operate-time tooling: a config-driven validator, a pre-commit hook, a deterministic map-of-content generator, a synthesis-status reporter, a link-graph and gap reporter, transparent git sync, and provider-agnostic Agent Skills for common workflows (session close, validation fix, synthesis, notes, ADRs, todos, weekly review, seed distillation). One config file, `.scripts/vault.config.json`, is the single source of truth for domains and the frontmatter contract. Read [`docs/ARCHITECTURE.md`](template/docs/ARCHITECTURE.md) (shipped into every vault) for why each piece is built the way it is.

Sensitive personnel data does not live in the vault at all. It goes in a separate private vault on a path no agent is configured to reach. Physical separation is the only robust control; a `confidential: true` flag is not access control.

## How it compares

auxmem shares DNA with several recent "markdown brain" projects. They landed on the same substrate (markdown, git, an `AGENTS.md` schema, entity and concept pages) because it is the right substrate. Where they differ is the bet about *where intelligence lives* and *what you have to run*.

| | substrate | where intelligence lives | you have to run | best at |
|---|---|---|---|---|
| **auxmem** | plain files | authoring discipline + a deterministic gate | nothing (files + git) | governed, portable, durable work memory |
| **Karpathy's LLM Wiki** | plain files | a compile step (agent synthesizes sources into pages) | an agent loop | absorbing large research corpora into synthesized pages |
| **GBrain** | files synced into Postgres | a query-time engine + self-wiring graph + 24/7 daemon | Postgres/pgvector, embeddings, a job queue, a daemon | retrieval quality and autonomous enrichment at scale |
| **OpenBrain** | a database | an MCP server + capture pipeline | Supabase/pgvector, a server | fast multi-channel capture into a shared store |

**vs [Karpathy's LLM Wiki](https://github.com/nashsu/llm_wiki).** Same substrate, opposite default. His pattern *compiles*: an agent ingests raw sources and synthesizes them into wiki pages as the normal runtime, and the community names the cost (information loss, summary drift, frozen mistakes). auxmem *authors*: humans own the ground-truth notes, and compile is a bounded, gated import step, not the operating principle. His default is better for turning a pile of papers into navigable understanding. auxmem's is better when a silently drifting fact is a liability. auxmem borrows his best idea, entity and concept pages, but requires them to cite sources and pass the validator, and it detects when they go stale.

**vs [GBrain](https://github.com/garrytan/gbrain).** GBrain shares auxmem's instinct that the git markdown repo is the system of record, then pours a production retrieval platform on top: hybrid vector plus keyword search, a self-wiring typed-edge graph, `think` for synthesized cited answers with gap analysis, and a nightly "dream cycle" of cron jobs that enrich and consolidate while you sleep. It is genuinely more capable at retrieval and autonomous enrichment (its own reported benchmarks are strong; they are self-reported). auxmem makes the opposite trade. It has no database, no embeddings, no daemon, so it cannot have any of a distributed system's failure modes, and no autonomous process ever rewrites your record. It keeps GBrain's most useful behaviors, the typed-edge graph and the gap analysis, reduced to a deterministic lint over the files, with no model and no server. If you need to answer questions across 100,000 pages, use GBrain. If you need a small memory that survives vendor churn and never mutates behind your back, that is auxmem.

**vs [OpenBrain](https://github.com/NateBJones-Projects/OB1).** OpenBrain is database-backed and capture-oriented, strong on getting signal in from many channels through an MCP server. auxmem is file-first and governance-oriented. Its own capture path is deliberately thin because capture belongs in your existing tools; the vault holds the durable state, not the firehose. auxmem's import recipes are hardened against the real edge cases of Claude, ChatGPT, and Gemini exports (branch selection, multimodal parts, title escaping, collisions) so seeding a vault is safe on the first try.

**The shared bet, and the divergence.** All four agree that markdown plus git is the right foundation for agent memory. The others treat that foundation as a *source* to compile into a system (a wiki the agent owns, or a database with a graph and a daemon). auxmem treats the foundation as the *product*. The moment memory becomes a database you inherit a database's failure modes and, if a daemon maintains it, a trust problem. For governed work memory, keeping the files as the whole system is the point, not a limitation.

## What auxmem is not

It is a personal-to-team-scale system, by design. It gives up query-time retrieval quality at massive scale and autonomous enrichment, in exchange for durability, auditability, portability, and the guarantee that nothing rewrites your record behind your back. It has no vector search, no server, no daemon. If your job is answering questions over tens of thousands of pages of external material, a system like GBrain fits better. If your job is keeping a durable, trustworthy, portable work memory, auxmem fits better.

It is also not a capture firehose. Capture in the tools you already use; let the vault hold what must persist.

## Design and philosophy

- [`docs/USAGE.md`](docs/USAGE.md) command reference, including the upgrade and fix workflows
- [`docs/IMPORTING.md`](docs/IMPORTING.md) seeding from AI exports and migrating an Obsidian vault
- [`template/docs/ARCHITECTURE.md`](template/docs/ARCHITECTURE.md) why each design choice is what it is
- [`template/docs/SYNTHESIS.md`](template/docs/SYNTHESIS.md) the governed synthesis loop (raw vs derived)
- [`template/docs/FIXING.md`](template/docs/FIXING.md) the tiered protocol for fixing validation failures

## Status

Building in public. This is the initial public release. The vault template is versioned independently of the CLI, and `auxmem upgrade` migrates existing vaults to newer template versions with a 3-way merge that never touches your notes. Feedback and issues welcome.

## License

MIT.
