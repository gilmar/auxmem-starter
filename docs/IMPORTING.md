# Importing

Two one-time paths, both run from AuxMem (not from inside an auxmem): seed an auxmem from AI provider exports, and migrate an existing Obsidian vault. Both end with the target auxmem's own validator as the gate.

Create the target auxmem first with `auxmem new`. Import writes into an existing auxmem.

## A. Seed from provider exports (Claude, ChatGPT, Gemini)

Two stages. A deterministic extractor normalizes exports into a staging corpus (outside any auxmem). Then a CLI agent distills that corpus into validated seed notes inside the auxmem.

### Get the exports
- Claude: Settings, Privacy, Export data. Produces `conversations.json`.
- ChatGPT: Settings, Data controls, Export. Produces `conversations.json`.
- Gemini: Google Takeout, My Activity, select Gemini Apps, JSON format. Note: Takeout gives your prompts, generally not the responses.

Provider memory features (what the app "knows about you") are NOT in these exports. Before leaving each app, ask it to write out everything it knows about you and your work, and save each answer into `seed-staging/manual/`. These manual dumps are the highest-signal input.

### Stage 1: extract to staging
```bash
mkdir -p seed-staging/manual   # paste the "what do you know about me" dumps here
auxmem seed claude_conversations.json  --staging ./seed-staging --since 2026-01-01
auxmem seed chatgpt_conversations.json --staging ./seed-staging --since 2026-01-01
auxmem seed MyActivity.json --provider gemini --staging ./seed-staging
```
The extractor auto-detects the provider, writes one file per conversation plus a triage `index.md`, and lives outside the auxmem (gitignored there).

Edge cases the extractor handles: ChatGPT exports store edited and regenerated messages as branches, and only the surviving branch (from `current_node`) is exported, so abandoned drafts are excluded. Multimodal parts and attachments are noted (e.g. `[attachment: spec.pdf]`) rather than silently dropped. Hidden system/tool messages are skipped. Titles containing colons, pipes, or quotes are safely escaped in frontmatter and the index. Same-title conversations get numbered suffixes. Empty conversations are dropped by `--min-messages`.

### Stage 2: distill into notes (agent step)
Run a CLI agent from the target auxmem, pointed at the distillation instructions in the starter:
```bash
cd ~/my-work        # the target auxmem
claude "Follow the instructions in /path/to/AuxMem/auxmem/importers/distill-seeds.md.
        The staging corpus is at /path/to/seed-staging."
```
The agent reads the manual dumps and triage index, selects conversations, and writes 15 to 30 current-state seed notes plus ADRs, MOCs, a bootstrap log, and open tasks. It synthesizes current state (not history), never copies transcripts verbatim, marks uncertainty, and flags any sensitive personnel content to a review list outside the auxmem rather than importing it.

### Finish
```bash
cd ~/my-work
python3 .scripts/gen_mocs.py
python3 .scripts/validate_auxmem.py --all
git add -A && git commit -m "seed auxmem from provider exports"
```
Replace placeholder summaries (grep for "Placeholder summary") as a follow-up, one folder at a time.

## B. Migrate an existing Obsidian vault

The obsidian-export pipeline is primary (better link fidelity, note embeds inlined). A single-script fallback needs no toolchain. Both read the target auxmem's config, so imported notes validate against that auxmem's domains.

Write a `map.json` mapping old folders to the new structure:
```json
{
  "folders": {"Projects/DataHub": "10-projects", "Meetings": "70-meetings"},
  "exclude": ["Templates"],
  "default_domain": "projects"
}
```

### Pipeline (recommended)
Install obsidian-export first. On a recent Rust toolchain: `cargo install obsidian-export --locked`. On Ubuntu's apt cargo (1.75): `cargo install obsidian-export --version 23.12.0 --locked`. Or use a release binary.
```bash
auxmem import-obsidian ~/old-vault --dest ~/my-work --map map.json --dry-run
auxmem import-obsidian ~/old-vault --dest ~/my-work --map map.json
```

### Single-script fallback (no toolchain)
```bash
auxmem import-obsidian ~/old-vault --dest ~/my-work --map map.json --no-pipeline --dry-run
auxmem import-obsidian ~/old-vault --dest ~/my-work --map map.json --no-pipeline
```

### After either
Read `~/my-work/00-inbox/migration-report.md` before committing. It lists unmapped links (now plain text), files needing manual handling (`00-inbox/import-manual/`), and frontmatter retrofits to review. Unmapped and ambiguous links degrade to plain text, never broken links, so the auxmem stays valid. `auxmem import-obsidian` runs the auxmem's validator and MOC generator automatically after a real (non-dry-run) import. Treat the first real import as a rehearsal on a scratch copy of the destination.
