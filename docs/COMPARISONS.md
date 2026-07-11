# How auxmem compares

auxmem shares DNA with several recent "markdown brain" projects. They landed on the same substrate (markdown, git, an `AGENTS.md` schema, entity and concept pages) because it is the right substrate. Where they differ is the bet about *where intelligence lives* and *what you have to run*.

| | substrate | where intelligence lives | you have to run | best at |
|---|---|---|---|---|
| **auxmem** | plain files | authoring discipline + a deterministic gate | nothing (files + git) | governed, portable, durable work memory |
| **Karpathy's LLM Wiki** | plain files | a compile step (agent synthesizes sources into pages) | an agent loop | absorbing large research corpora into synthesized pages |
| **GBrain** | files synced into Postgres | a query-time engine + self-wiring graph + 24/7 daemon | Postgres/pgvector, embeddings, a job queue, a daemon | retrieval quality and autonomous enrichment at scale |
| **OpenBrain** | a database | an MCP server + capture pipeline | Supabase/pgvector, a server | fast multi-channel capture into a shared store |

## vs Karpathy's LLM Wiki

Same substrate, opposite default. [His pattern](https://github.com/nashsu/llm_wiki) *compiles*: an agent ingests raw sources and synthesizes them into wiki pages as the normal runtime, and the community names the cost (information loss, summary drift, frozen mistakes). auxmem *authors*: humans own the ground-truth notes, and compile is a bounded, gated import step, not the operating principle. His default is better for turning a pile of papers into navigable understanding. auxmem's is better when a silently drifting fact is a liability. auxmem borrows his best idea, entity and concept pages, but requires them to cite sources and pass the validator, and it detects when they go stale.

## vs GBrain

[GBrain](https://github.com/garrytan/gbrain) shares auxmem's instinct that the git markdown repo is the system of record, then pours a production retrieval platform on top: hybrid vector plus keyword search, a self-wiring typed-edge graph, `think` for synthesized cited answers with gap analysis, and a nightly "dream cycle" of cron jobs that enrich and consolidate while you sleep. It is genuinely more capable at retrieval and autonomous enrichment (its own reported benchmarks are strong; they are self-reported). auxmem makes the opposite trade. It has no database, no embeddings, no daemon, so it cannot have any of a distributed system's failure modes, and no autonomous process ever rewrites your record. It keeps GBrain's most useful behaviors, the typed-edge graph and the gap analysis, reduced to a deterministic lint over the files, with no model and no server. If you need to answer questions across 100,000 pages, use GBrain. If you need a small memory that survives vendor churn and never mutates behind your back, that is auxmem.

## vs OpenBrain

[OpenBrain](https://github.com/NateBJones-Projects/OB1) is database-backed and capture-oriented, strong on getting signal in from many channels through an MCP server. auxmem is file-first and governance-oriented. Its own capture path is deliberately thin because capture belongs in your existing tools; the auxmem holds the durable state, not the firehose. auxmem's import recipes are hardened against the real edge cases of Claude, ChatGPT, and Gemini exports (branch selection, multimodal parts, title escaping, collisions) so seeding an auxmem is safe on the first try.

## The shared bet, and the divergence

All four agree that markdown plus git is the right foundation for agent memory. The others treat that foundation as a *source* to compile into a system (a wiki the agent owns, or a database with a graph and a daemon). auxmem treats the foundation as the *product*. The moment memory becomes a database you inherit a database's failure modes and, if a daemon maintains it, a trust problem. For governed work memory, keeping the files as the whole system is the point, not a limitation.
