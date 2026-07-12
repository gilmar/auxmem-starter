# payments-platform

an auxmem: a provider-independent work memory in plain markdown, built to be read and maintained by CLI AI agents (Claude Code, Codex, Gemini CLI) and synced with git. No provider lock-in, no proprietary formats, no plugins.

this auxmem was created by AuxMem. It is auxiliary memory, not a whole brain: capture happens in your existing tools and agents, and this auxmem holds the durable, governed, retrievable state they write to and read from.

## What is here
- A shallow, stable folder structure optimized for agent retrieval (grep, glob, frontmatter triage).
- A strict frontmatter schema enforced by a validator, so metadata stays clean and searchable.
- Transparent git sync with automatic conflict quarantine.
- todo.txt task management agents can read and write.
- Generated Maps of Content (no Dataview, no plugins).
- Provider-agnostic Agent Skills in `.skills/` for common workflows (linked to `.claude/skills`, `.codex/skills`, `.gemini/skills`, `.cursor/skills` by bootstrap).

## Working on a new machine
Clone the repo, then install the local hook and check dependencies:
```bash
git clone <this-auxmem-repo-url> ~/payments-platform && cd ~/payments-platform
./bootstrap.sh
```
`bootstrap.sh` is idempotent. It creates any missing folders from the config, links provider skill directories, installs the pre-commit hook (git hooks are not cloned), generates MOCs, and validates.

## Layout
```
AGENTS.md          canonical agent guide (CLAUDE.md and GEMINI.md point here)
.skills/           provider-agnostic Agent Skills (workflows for agents)
bootstrap.sh       per-machine installer (hooks, folders, validation)
.scripts/          operate-time tooling and auxmem.config.json (single source of truth)
docs/              SETUP, OPERATIONS, ARCHITECTURE
<NN>-<domain>/     subject-matter domains (defined in .scripts/auxmem.config.json)
60-decisions/      ADRs + index
70-meetings/       dated meeting and 1:1 notes
71-log/            append-only session/work logs
72-tasks/          todo.txt and done.txt task management
80-moc/            generated Maps of Content (agent entry points)
90-templates/      note templates
95-assets/         images and binaries
99-archive/        stale content, not searched by default
```

## The one rule that matters
the auxmem is the state. Models are interchangeable clients. Everything here is plain markdown, git, and open standards so that no single AI provider owns your context. Read `docs/ARCHITECTURE.md` for why each piece is built the way it is.

## Seeding and importing
Done from AuxMem (the tool that made this auxmem), not from here. See the starter's docs/IMPORTING.md.
