# Operations

How to run the auxmem day to day.

## The daily loop
1. Start an agent session from the auxmem root. The agent reads AGENTS.md, the home MOC, `72-tasks/todo.txt`, and recent logs.
2. Work. The agent creates and edits notes, updates tasks, and records decisions.
3. At session close the agent updates `72-tasks/todo.txt`, appends a log entry to `71-log/`, regenerates MOCs, validates, and commits.
4. Sync runs on its timer, or you run it manually.

You can also edit notes by hand in any text editor. The same rules and validator apply.

## Creating notes
Copy a template from `90-templates/` and fill the frontmatter. Filename convention: lowercase, hyphenated, with a type hint and date where relevant.
- Meetings and 1:1s: `2026-07-04-1on1-alex.md`, `2026-07-04-meeting-topic.md`
- Decisions: `adr-0007-cube-measure-naming.md`
- Findings: `finding-semantic-layer-gap-topic.md`
- Docs and profiles: `data-hub-mcp-server.md`, `stakeholder-revops.md`

The `summary` field is the most important line. Front-load it with the concrete nouns you would search for. Agents use it to judge relevance without reading the body, which saves tokens and time.

## Validation
The validator is the enforcement plane. It checks the frontmatter schema, controlled vocabularies, ISO dates, open-standard markdown only (no wikilinks, embeds, Dataview, Templater, or callouts), internal link resolution, and todo.txt grammar.
```bash
python3 .scripts/validate_auxmem.py --all         # whole auxmem (CI)
python3 .scripts/validate_auxmem.py path/to/note.md 72-tasks/todo.txt   # specific files
```
The pre-commit hook runs it on staged files automatically. To bypass once (rare): `git commit --no-verify`.

## Maps of Content
MOCs in `80-moc/` are generated from frontmatter, not hand-written. They are your and the agent's fast map of each domain.
```bash
python3 .scripts/gen_mocs.py           # rebuild all MOCs
python3 .scripts/gen_mocs.py --check   # CI: exit 1 if any MOC is stale
```
Do not edit MOC files by hand; edits are overwritten. Regenerate after adding or editing notes.

## Decisions (ADRs)
Durable decisions go in `60-decisions/` as ADRs (MADR format; use the template). Decisions are immutable. To change one:
1. Write a new ADR with the next number.
2. Mark the old one `status: superseded` and add a line pointing to the new one.
3. Update `60-decisions/index.md`.
This keeps an honest, time-ordered decision history and prevents an accepted decision from silently contradicting the current system.

## Tasks
Open tasks in `72-tasks/todo.txt`, archive in `72-tasks/done.txt`, todo.txt format. See AGENTS.md for the grammar and write rules. The validator enforces the grammar. Complete tasks in place, then move `x` lines to done.txt at session close. Never delete an open task; to drop one, complete it with `+cancelled`.

## Sync behavior
The sync script (`.scripts/auxmem-sync.sh`) is transparent and unconditional. It commits local changes (bypassing validation, since sync must never block), pulls with rebase and autostash, and pushes. Validation is enforced by agent and human commits (via the hook) and by CI, not by sync. The script uses bash 3.2–compatible syntax and a portable directory lock (no Linux-only `flock`).

Append-only files (`71-log/`, `00-inbox/`, `72-tasks/done.txt`) use `merge=union` so two devices appending never conflict.

### Conflict recovery
On a real content conflict (same line of the same non-append file edited on two devices), the sync script does NOT merge automatically. Instead:
- Your local divergence is pushed to a branch `sync-conflict/<host>-<timestamp>`.
- Local main is reset to match the remote.
- An alert note appears in `00-inbox/sync-conflict-*.md`.

To recover, from the auxmem:
```bash
git merge sync-conflict/<host>-<timestamp>   # or cherry-pick the commits you want
# resolve, verify, then:
git branch -d sync-conflict/<host>-<timestamp>
git push origin --delete sync-conflict/<host>-<timestamp>
```
This is deliberate. Automatic resolution of a genuine conflict is the kind of silent corruption git exists to prevent.

## Backups and safety
Git is the safety system, especially with agents writing. Commit frequently. If an agent corrupts a note, `git log` and `git checkout <sha> -- path` recover it. The remote is your offsite backup; keep it private.

## Health checks
```bash
python3 .scripts/validate_auxmem.py --all     # schema and format
python3 .scripts/gen_mocs.py --check         # MOC freshness
git status                                    # uncommitted state
systemctl --user list-timers                  # sync scheduled (if using systemd)
```

## Graph and gap report

`python3 .scripts/graph_report.py` gives a deterministic view of the auxmem's link graph, computed on demand from `sources:` frontmatter and markdown links. It reports hub notes (most referenced), orphan notes (no links in or out), source pairs drawn on together by multiple syntheses, and structural gaps such as tags used often with no page. Use `--note PATH` for one note's backlinks and neighbors, or `--json` for machine output. It is structural only: it surfaces islands and holes, it does not read for meaning or detect contradictions.
