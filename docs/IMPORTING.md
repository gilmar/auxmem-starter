# Importing

One-time path run from Koinome (not from inside a corpus): seed a corpus from AI provider exports. Distillation ends with the target corpus's own validator as the gate.

Create the target corpus first with `koinome new`.

## Seed from provider exports (Claude, ChatGPT, Gemini)

Two stages. A deterministic extractor normalizes exports into a staging area (outside any corpus). Then a CLI agent distills that corpus into validated seed notes inside the corpus.

### Get the exports
- Claude: Settings, Privacy, Export data. Produces `conversations.json`.
- ChatGPT: Settings, Data controls, Export. Produces `conversations.json`.
- Gemini: Google Takeout, My Activity, select Gemini Apps, JSON format. Note: Takeout gives your prompts, generally not the responses.

Provider memory features (what the app "knows about you") are NOT in these exports. Before leaving each app, ask it to write out everything it knows about you and your work, and save each answer into `seed-staging/manual/`. These manual dumps are the highest-signal input.

### Stage 1: extract to staging
```bash
mkdir -p seed-staging/manual   # paste the "what do you know about me" dumps here
koinome seed claude_conversations.json  --staging ./seed-staging --since 2026-01-01
koinome seed chatgpt_conversations.json --staging ./seed-staging --since 2026-01-01
koinome seed MyActivity.json --provider gemini --staging ./seed-staging
```
The extractor auto-detects the provider, writes one file per conversation plus a triage `index.md`, and lives outside the corpus (gitignored there).

Edge cases the extractor handles: ChatGPT exports store edited and regenerated messages as branches, and only the surviving branch (from `current_node`) is exported, so abandoned drafts are excluded. Multimodal parts and attachments are noted (e.g. `[attachment: spec.pdf]`) rather than silently dropped. Hidden system/tool messages are skipped. Titles containing colons, pipes, or quotes are safely escaped in frontmatter and the index. Same-title conversations get numbered suffixes. Empty conversations are dropped by `--min-messages`.

### Stage 2: distill into notes (agent step)
Run a CLI agent from the target corpus, pointed at the distillation instructions in the starter:
```bash
cd ~/my-work        # the target corpus
claude "Follow the instructions in /path/to/Koinome/koinome/importers/distill-seeds.md.
        The staging area is at /path/to/seed-staging."
```
The agent reads the manual dumps and triage index, selects conversations, and writes 15 to 30 current-state seed notes plus ADRs, MOCs, a bootstrap log, and open tasks. It synthesizes current state (not history), never copies transcripts verbatim, marks uncertainty, and flags any sensitive personnel content to a review list outside the corpus rather than importing it.

### Idempotency contract

**Seed extract (`koinome seed`):** Re-running the extractor on the same export with the same `--out` directory overwrites the same conversation filenames deterministically (duplicate titles receive numbered suffixes). The staging area is outside the corpus; re-import does not touch the corpus until stage 2 distillation.

```bash
cd ~/my-work
python3 .scripts/gen_mocs.py
python3 .scripts/validate_corpus.py --all
git add -A && git commit -m "seed corpus from provider exports"
```
Replace placeholder summaries (grep for "Placeholder summary") as a follow-up, one folder at a time.
