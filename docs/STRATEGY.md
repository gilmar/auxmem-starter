# Koinome Strategy

> **Knowledge in common.**

**Status:** Public
**Version:** 1
**Author:** Gilmar Souza
**Last updated:** 12 July 2026

Koinome is a solo, part-time, free and open-source project. This document is its strategy, published in the open because a project about inspectable knowledge should have an inspectable plan.

---

## 1. What Koinome is

Koinome is a governed knowledge system for humans and AI agents. Its unit is the **corpus**:

> A corpus is a portable, governed body of knowledge belonging to a person, agent, project, team, community, or organisation.

The name is the thesis: *koinos*, the Greek for "common," with the *-ome* suffix of genome and biome. The totality of what is held in common. Koinome exists so that knowledge can be **shared**: contributed, combined, merged, split, transferred, and federated across people, teams, and organisations, with AI agents mediating the meaning of every movement and deterministic systems governing its execution.

It begins as a local-first memory layer for AI agents, built on plain files you own. Agents propose; a deterministic validator decides; provenance travels with every record. No accounts, no telemetry. That local product is not a stepping stone to be discarded later. It is the foundation the whole thesis stands on, because sharing requires a unit that can be owned, bounded, and governed, and the corpus is that unit.

Koinome is the current point in a long line of work. The author has been evolving ideas about how to organise knowledge since 2014, when he began building a personal assistant named GERTY, and has kept a working system of his own in daily use through the years since. The first public iteration was a rewrite, in the open, of that private practice. Koinome carries the same core bet those years established: the files themselves are the product, and governance is enforced by deterministic tooling rather than by trust in a model. What is new in Koinome is the step from organising one person's knowledge to governing knowledge that is shared across boundaries.

## 2. Why it exists

Start with a cost the author paid personally. Across a long career spanning many companies, he built an enormous body of written knowledge, and each time he left an employer he destroyed all of it. That was the correct choice, and it remains so: with no governed way to separate what is legitimately one's own from what belongs to the employer, total destruction is the only safe response, and confidential material should never leave. But the fire took two things at once. It took the employer's material, as it should. And it took, alongside it, the general and portable lessons that law and contract never obliged anyone to surrender, because nothing could cleanly tell the two apart. What survived survived only in memory, which means it could not be transferred to anyone else, and much of it is simply gone. This is the loss Koinome is built to prevent: not the destruction of what must be destroyed, but the waste of everything legitimate that gets destroyed with it, and the death of knowledge that lives in a single head.

That personal loss is an instance of two general problems, with one root.

**AI context is fragmented and hard to trust.** Agents operate across isolated sessions, applications, providers, and models. The knowledge needed to act correctly is scattered across chat histories, repositories, trackers, and provider-specific memory features, so people re-explain the same project, the same constraints, the same decisions, in every session. The memory products built to fix this persist things silently, carry no provenance, and live in a provider's store under a provider's account.

**Knowledge crosses boundaries without governance.** A person contributes prior expertise to a team. A team combines individual knowledge into shared practice. An agent draws context from personal and project corpora at once. A consultant brings a method to a client. Someone leaves an organisation carrying legitimate learning while bound by confidentiality. Every one of these movements happens today, constantly, and every one of them is an ungoverned copy: no provenance, no rights, no record that it happened at all. Existing systems treat these situations as file access. That is not what they are.

Concretely, across one career: you maintain three corpora, personal, academic, and work. One person operates all three, but three different principals stand behind them. The personal corpus is yours outright. The academic corpus carries a university's terms. The work corpus belongs to an employer and is merely stewarded by you. First question: how does knowledge move between these three in a governed way? Second: when you leave that employer, how do you retain what you learned without retaining what contract and law say you cannot? Third: when you join the next organisation, how do you contribute what you legitimately carry, from day one, with a trail that protects the receiving side as much as it protects you? Koinome's answer to all three is one answer: govern the boundaries daily, and every later movement, including the hardest one, becomes routine.

The root is the same: there is no unit. Nothing in the current landscape can be owned, bounded, validated, and moved as a whole, so nothing can be shared as anything better than a paste.

**The author is the first user.** Koinome exists because its author works daily across multiple AI agents and several long-running projects, and needs a knowledge layer that survives sessions, survives provider switches, and can be inspected and corrected by hand. Every feature traces to a friction actually hit in that daily work. If Koinome stops earning its place in the author's own workflow, the project will say so honestly.

## 3. The claim

Koinome makes one structural claim about the current landscape:

> **Every AI memory system on the market today is single-principal by design. Mem0, Zep, Letta, LangMem, and the memory features of the major providers all assume one owner, one boundary, one authority. This is not a missing feature. It is the architecture.**

The named systems are named because the claim is checkable, not because their engineering is poor. Much of it is excellent. The claim is about what the architecture can represent.

And here is why it is a flaw rather than a simplification: **knowledge is inherently multi-principal.** It is created by one principal, contributed to another, combined with a third's, and carried across boundaries for as long as it is useful. An architecture with no unit of ownership cannot represent that movement, let alone govern it. You cannot share, merge, or split what has no boundary, no identity, no provenance, and no rights.

And no team is required for the claim to bite. One person is already a multi-principal system: a personal corpus owned outright, an academic corpus carrying a university's terms, a work corpus owned by an employer and merely stewarded by the person who fills it. Single-principal memory cannot represent one professional's ordinary week.

Two consequences follow:

1. **The corpus, not the account, is the durable unit of AI knowledge.** A corpus can be owned, inspected, validated, moved, and, above all, shared, independently of any tool, model, or host.
2. **AI mediates meaning; deterministic systems authorise and execute.** An agent may read scoped context, propose changes, and plan operations. Whether anything becomes canonical, or crosses a boundary, is decided by deterministic validation and human approval. This is the policy decision point / policy enforcement point separation long established in access control (XACML lineage, NIST SP 800-162), with a language model as the planner. Koinome names the prior art deliberately: it is an implementable architecture, not a slogan.

## 4. Knowledge in common: the operations

This is the heart of the project. Corpora relate without dissolving into one another, and knowledge moves between them through explicit, governed operations:

**Share. Contribute. Transfer. Merge. Split. Combine. Federate. Derive. Generalise. Publish. Revoke. Archive.**

These are semantic operations, not mechanical ones. "Share the parts of my personal corpus relevant to this project" is not a file copy: it requires judgement about relevance, implicit dependencies, sensitivity, and the minimum sufficient context for the recipient. Merging two corpora is not concatenating directories: it means reconciling duplicated concepts, competing claims, incompatible policies, and distinct histories. Koinome is not a wrapper around git commands. It operates on meaning, dependencies, authority, and policy.

That is why the operations are **agent-mediated**. The user expresses intent in natural language. An agent discovers the relevant records and their implicit dependencies, proposes scope and transformations, surfaces conflicts and uncertainty, and produces an inspectable plan. Then deterministic systems take over.

Every operation, at every scale, follows one lifecycle:

> **Intent → discovery → plan → policy evaluation → human approval → deterministic execution → receipt.**

Nothing crosses a corpus boundary silently. Every movement produces an operation receipt, and provenance, rights, and ownership survive the crossing. The agent that mediates an operation is never the authority that executes it.

**The scaling path is the same lifecycle at growing scale.** One person operating corpora that already answer to different principals, sharing selectively across their own boundaries under per-direction policy: what may flow from a personal corpus into a work corpus is not what may flow back. A team combining individual contributions into shared practice without erasing who contributed what. An organisation federating many corpora, retaining continuity when people leave, without pretending that connection means common ownership. Same unit. Same operations. Same guarantees.

**And the honest line:** almost all of this is design scope today, not shipped software. It proceeds through public RFCs (Section 10), it ships one governable operation at a time (Section 11), and this document will never blur the two. The reason to trust the ambition is that its foundation is being built first, and its first operation ships within the year.

## 5. Commitments

These commitments define the project. They are written to be easy to hold the project to.

- **Local-first.** A corpus is a directory of plain files. It works offline, forever, without Koinome running.
- **Individual use is account-free, forever.** No sign-up, no login, no hosted dependency, and no future scale of the project will ever retrofit one onto individual use.
- **No telemetry.** None. Not opt-out, not anonymised. The project measures itself through its author's own use and through what early users choose to report.
- **Human-approved persistence.** Nothing becomes canonical knowledge without deterministic validation and explicit approval.
- **Nothing crosses a boundary silently.** Every movement between corpora is an approved operation that leaves a receipt.
- **The AI proposes; it never decides.**
- **Complete and free.** The individual, local corpus tooling is and will remain complete, free, and open-source. It is not a trial, a limited community edition, or a funnel toward anything.
- **Portable by construction.** The canonical layer is CommonMark and YAML that remains readable and useful if Koinome is deleted tomorrow.

Commitments like these are easy to state and historically hard to keep, so Koinome makes them structural rather than rhetorical. The code is licensed under the Apache License 2.0. Contributions are accepted under the Developer Certificate of Origin, with no contributor licence agreement, which keeps copyright distributed across contributors and makes a future relicensing of the community's work practically impossible. The relicensing episodes of recent years were all enabled by concentrated copyright; Koinome removes that lever from everyone, including its author. The corpus format is open and specified, so anyone can implement it without permission. The Koinome name will be registered as a trademark for one purpose only: so the project can never be forced to rename.

## 6. Decisions

Koinome's own decision records use the format below. The project is self-hosting: its design decisions live in a Koinome corpus, and the key ones are reproduced here.

| # | Decision | Rationale | Status |
|---|----------|-----------|--------|
| D1 | Sharing is the point; the individual product is its foundation, not its substitute. | You cannot share, merge, or split what has no boundary, identity, provenance, or rights. v0 builds the unit of sharing and the smallest instance of the operation lifecycle. | Accepted |
| D2 | The corpus is the product unit. | Ownership, portability, validation, governance, and exchange need a durable unit. Accounts and indexes are not it. | Accepted |
| D3 | Canonical knowledge is plain files; every derived representation is rebuildable. | The durable record must survive the disappearance of any service, model, index, or Koinome itself. | Accepted |
| D4 | AI mediates; deterministic systems validate, authorise, and execute. | Trust boundaries must be testable and auditable. Probabilistic components cannot be the final authority on what is true or what may move. | Accepted |
| D5 | Corpus operations are semantic, not mechanical. | Sharing, merging, and splitting operate on meaning, dependencies, authority, and policy, not on files and diffs. | Accepted |
| D6 | License: Apache-2.0. Contributions: DCO. No CLA. | Maximum adoption, patent safety, and a structural guarantee against relicensing. | Accepted |
| D7 | Standards before invention. | PROV, ODRL, Verifiable Credentials, JSON Schema, and MCP already solve most of what Koinome needs. Invention is reserved for genuine gaps. | Accepted |
| D8 | No accounts for individual use, no telemetry, ever. | The stance is the product. It must hold even where it makes the author's life harder. | Accepted |
| D9 | The author is the first user; every feature traces to a logged friction. | Tools built on genuine daily need survive. The friction log is public devlog material. | Accepted |
| D10 | Ambitious scope ships as RFCs before code, and ships one governable operation at a time. | Design proposals can be reviewed and retracted cheaply. Shipped operations must arrive with their full lifecycle: plan, policy, approval, receipt. | Accepted |
| D11 | The benchmark measures integrity and publishes all results, including unfavourable ones. | A benchmark that flatters its author's tool deserves to be dismissed. | Accepted |

## 7. Design principles

1. **The corpus is the unit.** Created, owned, validated, shared, moved, and archived as a whole.
2. **Files are canonical.** Indexes, embeddings, summaries, and bundles are derived, and always rebuildable.
3. **One lifecycle for every movement.** From an agent's proposal to an organisational merge: intent, plan, policy, approval, receipt.
4. **No silent rewriting, no silent crossing.** Material changes and boundary movements are attributable, inspectable, reviewable, and reversible.
5. **Provenance before confidence.** A record shows why it exists and what supports it, and keeps showing it after it moves.
6. **Rights travel with knowledge.** Ownership, attribution, and permitted use survive copying, merging, and derivation.
7. **Boundaries stay visible.** Connected corpora cooperate without collapsing into one undifferentiated store.
8. **Standards before invention.** Divergences are documented and mapped back where possible.
9. **Dogfood before feature.** If no logged friction justifies it, it waits.
10. **Proportional governance.** A grocery note does not need the ceremony of an architecture decision. Rigour scales with importance.
11. **Honest scope.** What is design and what is shipped is always clearly separated.

## 8. What is being built: v0.x

v0 is the sharing protocol at its smallest scale. Every primitive in it exists because sharing requires it: durable corpus identity makes a corpus addressable; provenance makes knowledge trustworthy after it moves; rights metadata makes movement governable; and the proposal flow is the operation lifecycle itself, with two parties. The first boundary Koinome governs is the one between a model's context and your canonical corpus. An agent proposing a record to you is already a knowledge movement across a boundary, mediated by an agent, decided deterministically.

One artifact: **the Koinome CLI plus MCP server, at daily-driver quality.** Five things, and only five:

1. **Corpus init and manifest.** Durable corpus identity independent of filesystem path or git remote, with ownership and stewardship declared explicitly, because a corpus's owner and its operator are not always the same party. Per-direction boundary policies live in the manifest from day one, inert until the first operation ships and enforced from then on. Six minimal record types: decision, claim, state, policy, instruction, source.
2. **The deterministic validator.** Schema correctness, required metadata, broken references, missing sources, supersession rules, scope violations.
3. **The MCP server.** Scoped context assembly exposed as resources; the proposal flow exposed as tools. MCP is how agents use Koinome, across any client that speaks the protocol.
4. **Provenance on records.** PROV-mapped fields in frontmatter; attribution and derivation travel with every record.
5. **One polished example corpus and a recorded demo.**

### The 90-second demo

The demo is the anchor for every build decision, because it shows the one thing no other memory tool shows: a visible trust boundary.

1. `koinome init` creates a corpus; the manifest shows identity and policy.
2. An agent, via MCP, requests context and receives a scoped bundle. It acts correctly without re-explanation.
3. The agent proposes a new decision record from the conversation.
4. The validator blocks it: the proposal contradicts an accepted decision without superseding it, and lacks a source.
5. The agent revises. The human reviews the diff and approves. Provenance shows what was derived from what, and who accepted it.
6. A second, different agent client mounts the same corpus and continues seamlessly.

### The demo after that

The first cross-corpus operation, planned for the end of year one (Section 11), has its demo already written: *"Share what is relevant to this project from my personal corpus into the project corpus, excluding anything marked private."* The agent discovers the records and their dependencies, proposes a plan showing what is included, what is excluded, and why. The validator checks it against policy. The human approves. The records move with their provenance intact, and a receipt records the operation. That is the thesis, on one machine, in one minute.

### The honest competitor

Koinome's real near-term competitor is not any memory product. It is a folder of markdown plus an AGENTS.md file plus git, which already delivers most of the solo context-persistence value at zero schema cost. If that works for you, keep it. But the folder ends where the thesis begins: it has no identity, no provenance, no rights, and no policy, so it cannot be shared under governance, merged with its history intact, or split without losing what came from where. For one person, Koinome must still earn the difference on the margin, at a setup cost low enough to be worth it. Concretely: **under fifteen minutes from install to the first agent-consumed context**, or the design has failed.

### Quality bar for v0.1

v0.1 is released only after the author has used Koinome daily for thirty consecutive days, across at least two corpora and two different agent clients, in real work. Not demos. Not tests.

### Explicitly deferred

Multi-party coordination, synchronisation between people, staleness detection beyond trivial checks, importers and exporters beyond basics, rights enforcement, and every operation except the first. The data primitives they will need (durable identity, provenance fields, rights metadata stored as inert ODRL-shaped frontmatter) are stabilised now so the format does not break later.

## 9. Standards before invention

Every primitive Koinome needs that already has an open standard uses the open standard. This is not only economy; it is the sharing thesis in practice. PROV and ODRL exist precisely so that provenance and rights can survive movement between systems that do not share an implementation.

| Koinome primitive | Standard | Usage |
|---|---|---|
| Provenance | W3C PROV (PROV-DM / PROV-O) | Frontmatter fields aligned to `wasDerivedFrom`, `wasAttributedTo`, `wasGeneratedBy`, `generatedAtTime`. Export to PROV-O is a supported path. |
| Rights metadata | W3C ODRL Information Model 2.2 | Permission, prohibition, and duty in ODRL vocabulary. Inert metadata in v0; enforced as operations ship. |
| Contribution receipts | W3C Verifiable Credentials 2.0 | Issuer, credentialSubject, proof. RFC-only for now. |
| Policy architecture | ABAC with PDP/PEP separation (XACML lineage, NIST SP 800-162) | The validator is the decision and enforcement point; the LLM is a planner submitting requests. |
| Agent interface | Model Context Protocol | Resources for scoped context; tools for proposals and, later, operation plans. |
| Record format | CommonMark + YAML frontmatter | The human-readable canonical layer. |
| Schemas | JSON Schema | Record types, the manifest, and operation plans and receipts, validated deterministically. |
| Licence metadata | SPDX identifiers | In the manifest and on records where relevant. |

Illustrative frontmatter for a decision record:

```yaml
id: dec-2026-0714-mcp-first
type: decision
status: accepted
prov:wasAttributedTo: "gilmar"
prov:generatedAtTime: "2026-07-14T21:40:00-03:00"
prov:wasDerivedFrom: ["src-2026-0712-design-review"]
supersedes: null
odrl:permission: [{ action: "use", assignee: "self" }]
```

The rule: invent only where no standard exists. The corpus manifest, the proposal and approval flow, and the operation plan and receipt shapes are inventions; each documents its divergence and maps back to PROV activities where possible.

## 10. Design before build: the RFC backlog

The full ambition of Koinome lives in design documents, published as RFC-labelled proposals, open to review and collaboration, and honestly separated from shipped software:

- **Cross-corpus operation semantics**: precise definitions for share, contribute, transfer, merge, split, combine, federate, derive, generalise, publish, revoke, and archive. First in the queue, because the first operation ships against it.
- **Operation plans and operation receipts**: the inspectable proposal before, and the durable audit record after, every movement.
- **Rights-envelope enforcement** (ODRL): how permissions, prohibitions, and duties are evaluated when knowledge moves.
- **Exit review and generalisation**: how knowledge legitimately leaves one boundary for another, with an auditable, human-approved trail. The design premise is that exit is a daily condition rather than an event: lessons are generalised continuously, each carrying provenance by reference rather than by content, so the review at departure is a sweep of receipts instead of a scramble. Koinome does not adjudicate ownership and is not a substitute for contracts; an auditable trail is the honest offering.
- **Contribution receipts as Verifiable Credentials.**
- **Federation across corpora without centralisation**: discovery and coordinated use without a canonical central store.

Specifications can be retracted and improved cheaply. Shipped operations cannot, which is why each one arrives only with its full lifecycle attached.

## 11. Roadmap: the next twelve months

Koinome is a part-time project, worked a few hours a week. Months may slip; the sequence will not.

**Months 0 to 1: Foundation.** Repository published under the Koinome name with history preserved. Apache-2.0 and DCO in place, security.txt live, package names claimed by publishing the real CLI skeleton. Corpus format v0: manifest, six record types, PROV-mapped frontmatter, inert ODRL rights metadata, JSON Schemas.

**Months 1 to 4: The unit.** Validator and CLI core. MCP server: scoped context resources and proposal-flow tools. Daily dogfooding begins on the project's own corpus and the author's personal corpora, with a running friction log.

**Months 4 to 6: Prove and release.** The thirty-day daily-use quality bar for v0.1. Example corpus polished; the demo recorded. Public release, accompanied by the first essay: the single-principal claim, in full.

**Months 6 to 9: Iterate, and design the operations.** Friction-driven changes only. A handful of early users invited; time-to-value measured directly against the fifteen-minute target. The cross-corpus operations RFC published: operation semantics, plan and receipt schemas. Benchmark harness built.

**Months 9 to 12: The first operation, and the claim made executable.** The first cross-corpus operation ships: agent-mediated selective **share** between two corpora operated by the same person. One operator, one machine, no accounts, no server, and quite possibly more than one principal, because one professional's corpora usually answer to more than one owner. The complete lifecycle: intent, discovery, plan, policy, approval, execution, receipt. Benchmark results published with the harness. The next year's shape decided from evidence.

## 12. How to judge this project

Public, testable criteria. Hold Koinome to them:

1. The author uses it daily. The friction log is public; if dogfooding lapses, the log will show it.
2. A new user reaches first agent-consumed context in under fifteen minutes.
3. No telemetry appears, ever, in any form.
4. The format remains independently implementable from the specification alone.
5. Every shipped cross-corpus movement produces an inspectable plan before and a receipt after. If one does not, the design has failed.
6. The benchmark ships with public harness code and publishes results Koinome loses.
7. Design proposals and shipped software are never blurred.

## 13. Expectations

Koinome is design-driven and part-time maintained. Issues and RFC feedback are welcome; response times will be honest rather than fast. The code surface is kept deliberately small, because a small surface is what one careful person can keep trustworthy. The project continues for as long as it earns its place in its author's daily work, which is a floor that does not depend on stars, trends, or anyone's roadmap but this one.

## 14. Non-goals

Koinome is not run as a startup, and it has no roadmap to monetise the people who use it. Whether a company is ever built around the project is a question left open, but the answer cannot touch what is written here: any such company would build around the open project, never inside it. The license guarantees this rather than merely promising it. The core is Apache-2.0 under distributed copyright, so it cannot be relicensed or withdrawn, and individual use stays free and account-free by structure. A future entity could offer new work built on top; it could not complete, unlock, or reclaim the open foundation, because that foundation is already beyond anyone's power to close, including the author's. Individual use will never require a hosted service. It is not a note-taking app, a task manager, an agent framework, a RAG framework, a source-control replacement, or an enterprise content suite. It does not adjudicate legal ownership and does not substitute for contracts or confidentiality agreements. It collects no data about its users. It specifies twelve cross-corpus operations and ships them only as fast as each can arrive with its full lifecycle, starting with one. And it never treats connected corpora as one undifferentiated pool: connection does not imply common ownership, automatic merging, or policy erasure.

## 15. North star

A person installs Koinome and creates a useful corpus in minutes, in an open format, with no account. Their agents consult it before acting and propose to it after learning. When knowledge needs to cross a boundary, they say what they intend, an agent works out what that means, and a plan, a policy check, an approval, and a receipt make the movement safe. The same unit and the same lifecycle carry from one person's two corpora to a team's shared practice to an organisation's federation, and provenance, rights, and ownership survive every crossing. The corpus outlives every tool that touches it, including this one.

The creed, which survives every version of this document:

> **The corpus belongs to you. The AI proposes. Deterministic systems decide. And knowledge moves only in the open.**
