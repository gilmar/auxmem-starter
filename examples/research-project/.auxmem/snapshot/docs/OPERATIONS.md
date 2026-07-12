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

Read-only conformance check (for humans and CI; never modifies files):
```bash
python3 .scripts/check_auxmem.py              # validation + MOC freshness
auxmem check PATH                             # same, from outside the auxmem
python3 .scripts/check_auxmem.py --manifest   # also verify managed tooling hashes
python3 .scripts/check_auxmem.py --git        # also require a clean working tree
```

To regenerate stale MOCs before committing, use `python3 .scripts/gen_mocs.py` or `auxmem doctor PATH` (doctor may write files; check does not).

```bash
python3 .scripts/validate_auxmem.py --all         # validation only
python3 .scripts/validate_auxmem.py path/to/note.md 72-tasks/todo.txt   # specific files
```
The pre-commit hook validates the staged git index snapshot automatically. To bypass once (rare): `git commit --no-verify`.

## Continuous integration
New auxmems include `.github/workflows/auxmem-check.yml`. On each push or pull request it installs PyYAML and runs `python3 .scripts/check_auxmem.py`. Enable GitHub Actions on your remote to activate it.

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
The sync script (`.scripts/auxmem-sync.sh`, implemented by `.scripts/auxmem_sync.py`) keeps devices aligned without weakening the validation gate on the canonical branch.

State machine:
1. Resolve the current git branch and its upstream remote (override with `AUXMEM_SYNC_BRANCH` / `AUXMEM_SYNC_REMOTE`).
2. Acquire a per-auxmem lock at `.git/auxmem-sync.lock/` (not a global `/tmp` lock).
3. Stage pending changes and validate the git index snapshot before any canonical commit.
4. **Valid pending auxmem changes:** verified `git commit` (pre-commit hook runs), `git pull --rebase --autostash`, read-only `check_auxmem.py`, then push.
5. **Invalid pending auxmem changes:** quarantine commit on `sync-invalid/<host>/<timestamp>`, push that branch when a remote exists, reset the canonical branch to its prior tip, write an alert (`00-inbox/sync-invalid-*.md` when a domain exists, else `.auxmem/alerts/`), exit `3`.
6. **Rebase conflict:** abort the rebase, preserve local commits on `sync-conflict/<host>/<timestamp>`, push that branch, reset canonical to the remote tip, write a conflict alert, exit `3`.

Sync never uses `git commit --no-verify` on the canonical branch. Quarantine commits are the only exception, and they live on side branches.

Append-only files (`71-log/`, `00-inbox/`, `72-tasks/done.txt`) use `merge=union` so two devices appending rarely conflict.

### Invalid-state recovery
When validation fails on pending changes:
- Inspect `00-inbox/sync-invalid-*.md` (or `.auxmem/alerts/sync-invalid-*.md`).
- Fetch and check out the named `sync-invalid/...` branch.
- Fix validation issues, regenerate MOCs, validate, then merge or cherry-pick onto your canonical branch.

### Conflict recovery
On a real content conflict (same line of the same non-append file edited on two devices), sync does NOT merge automatically. Instead:
- Your local divergence is pushed to `sync-conflict/<host>/<timestamp>`.
- The canonical branch is reset to match the remote.
- An alert appears in `00-inbox/sync-conflict-*.md` (or `.auxmem/alerts/`).

To recover, from the auxmem:
```bash
git merge sync-conflict/<host>/<timestamp>   # or cherry-pick the commits you want
# resolve, verify, then:
git branch -d sync-conflict/<host>/<timestamp>
git push origin --delete sync-conflict/<host>/<timestamp>
```
This is deliberate. Automatic resolution of a genuine conflict is the kind of silent corruption git exists to prevent.

## Backups and safety
Git is the safety system, especially with agents writing. Commit frequently. If an agent corrupts a note, `git log` and `git checkout <sha> -- path` recover it. The remote is your offsite backup; keep it private.

## Health checks
```bash
python3 .scripts/check_auxmem.py           # read-only conformance (CI)
auxmem check PATH                          # same, from the AuxMem CLI
auxmem doctor PATH                         # regenerate MOCs, then validate
python3 .scripts/validate_auxmem.py --all  # validation only
python3 .scripts/gen_mocs.py --check       # MOC freshness only
git status                                 # uncommitted state
systemctl --user list-timers               # sync scheduled (if using systemd)
```

## Graph and gap report

`python3 .scripts/graph_report.py` gives a deterministic view of the auxmem's link graph, computed on demand from `sources:` frontmatter and markdown links. It reports hub notes (most referenced), orphan notes (no links in or out), source pairs drawn on together by multiple syntheses, and structural gaps such as tags used often with no page. Use `--note PATH` for one note's backlinks and neighbors, or `--json` for machine output. It is structural only: it surfaces islands and holes, it does not read for meaning or detect contradictions.
