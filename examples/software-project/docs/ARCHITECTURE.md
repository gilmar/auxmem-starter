# Architecture

Why this auxmem is built the way it is. Read this before changing the design.

## The thesis
Business context and memory must outlive any single AI provider. Provider apps hold your state (conversation history, memory features) in systems you do not own, in formats you cannot export cleanly. this auxmem inverts that. the auxmem is the state. Models are interchangeable clients that read and write it. Switching from one provider to another, or running several at once, costs nothing because nothing about your knowledge lives inside a provider.

Concretely: everything is plain markdown, git, and open standards (CommonMark, GFM tables, YAML frontmatter, todo.txt, MADR, AGENTS.md). All of these predate current AI tools and will outlive them.

## Optimized for how agents actually retrieve
CLI agents (Claude Code, Codex, Gemini CLI) navigate an auxmem with filesystem primitives: they read the directory tree, grep and glob, and read specific files on demand. They do not build a vector index by default. Three consequences shape the design:
1. Descriptive filenames and folder names are semantic signals, not just labels. Hence the naming conventions.
2. The frontmatter `summary` field lets an agent judge a note's relevance without reading the body. It is the highest-leverage token saver in the auxmem.
3. Shallow structure beats deep nesting. Few top-level folders, flat within them, filenames and frontmatter doing the fine-grained discrimination that deep folders would otherwise do.

For literal lookups (a name, a metric, a date), grep is free and precise. Reserve semantic search for conceptual questions, and add it only if grep plus summaries stop being enough. See the token-reduction note at the end.

## Admission plane vs enforcement plane
The central pattern, borrowed from software supply-chain governance. Instructions written in prose (AGENTS.md) are the admission plane: they tell agents what to do and mostly work. But an instruction an agent can read is an instruction it can ignore. Anything that MUST hold is enforced mechanically:
- The validator (`validate_auxmem.py`) plus the git pre-commit hook are the enforcement plane for schema and format. Prose asks; the hook refuses.
- The single config file (`.scripts/auxmem.config.json`) is the source of truth. The validator, folder bootstrap, and MOC generator all read it. Change the config, and the constraints change everywhere at once.

This is an enabling-constraint design. The structure is a constraint that makes the compliant path the low-friction path. Templates pre-fill the schema, so filling it correctly is easier than not. MOCs are generated, so the map is always current without hand-maintenance. the auxmem steers behavior so you do not have to.

## Why open standards over proprietary note apps
Some editors add power features (wikilinks, `![[embeds]]`, Dataview, Templater, callouts) that are non-standard. They tie the auxmem to one tool and, in the case of Dataview, embed executable queries that an agent might parse as fact. the auxmem bans all of it in favor of relative markdown links and generated MOCs. The cost is that no tool auto-maintains links on rename; the mitigation is stable filenames plus an optional markdown LSP (Marksman). ADR-0001 records this decision.

## Why generated MOCs, not dashboards
Plugin dashboards are convenient but live inside notes as non-standard queries and only render in one editor. `gen_mocs.py` reads frontmatter across the auxmem and writes plain-markdown MOCs as derived, committed artifacts. Same information, portable everywhere, and greppable. MOCs are agent entry points first, human navigation second.

## Sync as a separate plane from validation
Sync must run often enough that devices do not silently diverge. Validation must gate what lands on the canonical branch. Resolution: sync stages pending work, validates the git index snapshot, and only then creates a verified canonical commit. Invalid pending state is quarantined on a side branch while the canonical tip is restored. Real rebase conflicts are preserved on another side branch rather than auto-merged. Automatic resolution of a genuine content conflict is exactly the silent corruption git exists to prevent.

## The sensitive-data boundary
This is the one place to be strict. An LLM with a filesystem path to a file can read it. A frontmatter flag like `confidential: true` is advisory, not access control. Therefore performance reviews, terminations, compensation, and health records about individuals do NOT live in this auxmem at all. They belong in a separate private auxmem on a path no AI tool is configured to reach. The AI-facing auxmem holds only non-sensitive derivatives (a process checklist, a de-identified capacity note), never individual records. AGENTS.md instructs agents to refuse such requests and, during imports, to flag sensitive source files without importing them. Physical path separation is the only robust control.

## Multi-model write safety
Different models follow conventions with different fidelity, so multi-agent write access multiplies corruption risk. Two mitigations: git with frequent commits is the safety system (not just hygiene), and where practical, designate one agent as the writer and others as readers.

## Token efficiency (deferred by design)
The structure already reduces tokens: frontmatter summaries enable triage without full reads, generated MOCs prevent blind folder scans, and AGENTS.md is kept short. Further optimization (a provider-agnostic gateway and meter like LiteLLM, local semantic search like QMD, routing cheap tasks to local models via Ollama) is intentionally left until real usage data shows where tokens actually go. Measure first. Do not compress notes at rest; readability is the point.

## What to preserve if you change things
- Keep the config as the single source of truth. Do not hard-code vocabularies back into scripts.
- Keep validation mechanical and separate from sync.
- Keep the sensitive-data boundary physical.
- Keep notes short, atomic, and richly cross-linked with relative links.
- Keep AGENTS.md under ~150 lines; instruction-following degrades past a couple hundred instructions.

## Influences

The reliability frame behind this design comes from Adrian Hornsby's essay ["We're Building Agents on a Foundation Most Engineers Have Never Heard Of"](https://newsletter.resiliumlabs.com/p/were-building-agents-on-a-foundation) (Resilience Bites). In his terms: the auxmem is the data plane, kept statically stable, the part that keeps working when everything clever is down. Every intelligent process, agents included, is control-plane automation standing on top of it, an optimization the record must never depend on to survive. His routing rule maps directly onto the auxmem's asymmetry: reversible, read-heavy, high-volume work goes to the agent and fails open; the irreversible act of committing a fact to the record is gated and fails closed.
