#!/usr/bin/env python3
"""Materialize sanitized reference auxmems under examples/ (AUX-012).

Run after template changes:
  uv run python examples/build_references.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tests.helpers import (  # noqa: E402
    gen_mocs,
    init_git_repo,
    note_with_fm,
    run_git,
    scaffold_auxmem,
    validate_auxmem,
    write_note,
)

EXAMPLES = REPO_ROOT / "examples"
REFERENCE_NAMES = ("software-project", "consulting-engagement", "research-project")


def _note(body: str, **fields) -> str:
    return note_with_fm(body, **fields)


def _write(dest: Path, rel: str, body: str, **fields) -> None:
    write_note(dest, rel, _note(body, **fields))


def _commit(dest: Path, message: str) -> None:
    run_git(["add", "-A"], cwd=dest)
    result = run_git(["commit", "-m", message], cwd=dest)
    if result.returncode != 0 and "nothing to commit" not in result.stdout + result.stderr:
        raise RuntimeError(f"git commit failed: {result.stdout}\n{result.stderr}")


def _finalize(dest: Path, *, git_history: bool = True) -> None:
    gen_mocs(dest)
    validation = validate_auxmem(dest)
    if validation.returncode != 0:
        raise RuntimeError(
            f"reference auxmem failed validation:\n{validation.stdout}\n{validation.stderr}"
        )
    if git_history:
        if (dest / ".git").exists():
            shutil.rmtree(dest / ".git")
        init_git_repo(dest)
        _commit(dest, "Initial reference auxmem content")
        _commit(dest, "Add superseding ADR and synthesis layer")
    # Do not ship .git inside examples/ — history is reproducible via build script.
    if (dest / ".git").exists():
        shutil.rmtree(dest / ".git")


def build_software_project(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    scaffold_auxmem(
        dest,
        name="payments-platform",
        domains=["10-engineering=engineering", "20-product=product"],
    )

    _write(
        dest,
        "10-engineering/platform-architecture.md",
        "The payments platform runs as Python services behind an API gateway. "
        "See [ADR-0002](../60-decisions/adr-0002-service-boundaries.md) for the current boundary model.",
        title="Payments platform architecture",
        summary="Overview of the payments platform service layout and runtime dependencies for engineering onboarding.",
        type="project-doc",
        status="active",
        domain="engineering",
        created="2026-06-01",
        updated="2026-06-15",
        tags=["architecture", "payments"],
    )
    _write(
        dest,
        "20-product/q3-roadmap.md",
        "Q3 priorities: checkout latency reduction, reconciliation dashboard, and vendor failover drills.",
        title="Q3 product roadmap",
        summary="Quarterly product priorities for the payments platform team and stakeholder alignment.",
        type="project-doc",
        status="active",
        domain="product",
        created="2026-06-05",
        updated="2026-06-10",
    )
    _write(
        dest,
        "60-decisions/adr-0001-monolith-stack.md",
        "## Status\nSuperseded by [ADR-0002](adr-0002-service-boundaries.md).\n\n"
        "## Context\nEarly delivery favored a single deployable artifact.\n\n"
        "## Decision\nRun the payments API as one monolith.\n\n"
        "## Consequences\nFast iteration, later scaling limits.",
        title="ADR-0001 Monolith stack",
        summary="Original decision to ship the payments API as a single monolith for speed to market.",
        type="adr",
        status="superseded",
        domain="engineering",
        created="2026-05-01",
        updated="2026-06-12",
    )
    _write(
        dest,
        "60-decisions/adr-0002-service-boundaries.md",
        "## Status\nAccepted. Supersedes [ADR-0001](adr-0001-monolith-stack.md).\n\n"
        "## Context\nTraffic growth and team parallelism require clearer boundaries.\n\n"
        "## Decision\nSplit checkout, ledger, and reconciliation into separate services.\n\n"
        "## Consequences\nMore operational overhead, better isolation.",
        title="ADR-0002 Service boundaries",
        summary="Accepted decision to split the payments platform into checkout, ledger, and reconciliation services.",
        type="adr",
        status="active",
        domain="engineering",
        created="2026-06-12",
        updated="2026-06-12",
    )
    _write(
        dest,
        "70-meetings/2026-06-15-architecture-review.md",
        "Attendees: platform, product, SRE.\n\nReviewed ADR-0002 rollout plan and latency benchmarks from vendor sources.",
        title="Architecture review 2026-06-15",
        summary="Architecture review covering ADR-0002 rollout, latency benchmarks, and open vendor contradictions.",
        type="meeting",
        status="done",
        domain="engineering",
        created="2026-06-15",
        updated="2026-06-15",
    )
    _write(
        dest,
        "71-log/2026-06-20-synthesis-session.md",
        "Synthesized vendor latency sources into `85-synthesis/`. Contradiction left unresolved pending SRE review.",
        title="Synthesis session 2026-06-20",
        summary="Log entry for a synthesis session over vendor latency benchmarks and unresolved contradictions.",
        type="log",
        status="done",
        domain="engineering",
        created="2026-06-20",
        updated="2026-06-20",
    )
    todo = dest / "72-tasks" / "todo.txt"
    existing = todo.read_text(encoding="utf-8").rstrip("\n")
    todo.write_text(
        existing
        + "\n(A) Reconcile vendor latency contradiction ref:05-sources/latency-benchmark-vendor-a.md\n"
        + "(B) Schedule failover drill ref:60-decisions/adr-0002-service-boundaries.md\n",
        encoding="utf-8",
    )
    _write(
        dest,
        "05-sources/latency-benchmark-vendor-a.md",
        "Vendor Alpha claims p99 checkout latency of **100ms** under nominal load.",
        title="Vendor Alpha latency benchmark",
        summary="Source capture of Vendor Alpha published latency benchmark for checkout p99 latency.",
        type="source",
        status="active",
        domain="engineering",
        created="2026-06-01",
        updated="2026-07-10",
    )
    _write(
        dest,
        "05-sources/latency-benchmark-vendor-b.md",
        "Vendor Beta reports p99 checkout latency of **50ms** on the same workload profile.",
        title="Vendor Beta latency benchmark",
        summary="Source capture of Vendor Beta published latency benchmark conflicting with Vendor Alpha.",
        type="source",
        status="active",
        domain="engineering",
        created="2026-06-02",
        updated="2026-06-02",
    )
    _write(
        dest,
        "85-synthesis/entity/vendor-alpha.md",
        "Vendor Alpha provides the primary gateway integration.\n\n"
        "## Open questions and contradictions\n"
        "Vendor Beta benchmark disagrees on p99 latency (50ms vs 100ms). Unresolved.",
        title="Vendor Alpha",
        summary="Synthesized entity page for Vendor Alpha with an unresolved latency contradiction across sources.",
        type="entity",
        status="active",
        domain="engineering",
        synthesis="generated",
        review="needed",
        sources=["05-sources/latency-benchmark-vendor-a.md", "05-sources/latency-benchmark-vendor-b.md"],
        generated_at="2026-06-01",
        created="2026-06-01",
        updated="2026-06-01",
    )
    _write(
        dest,
        "85-synthesis/concept/checkout-latency.md",
        "## Open questions and contradictions\n"
        "- Vendor Alpha: 100ms p99\n"
        "- Vendor Beta: 50ms p99\n"
        "Contradiction unresolved; do not treat either as authoritative.",
        title="Checkout latency targets",
        summary="Synthesized concept page documenting conflicting checkout latency claims across vendor sources.",
        type="concept",
        status="active",
        domain="product",
        synthesis="generated",
        review="needed",
        sources=["05-sources/latency-benchmark-vendor-a.md", "05-sources/latency-benchmark-vendor-b.md"],
        generated_at="2026-06-15",
        created="2026-06-15",
        updated="2026-06-15",
    )
    _finalize(dest)


def build_consulting_engagement(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    scaffold_auxmem(
        dest,
        name="northwind-engagement",
        domains=["10-engagement=engagement", "20-client=client"],
    )

    _write(
        dest,
        "10-engagement/engagement-charter.md",
        "Northwind Retail transformation engagement. Governance findings live under `20-client/`.",
        title="Engagement charter",
        summary="Charter for the Northwind Retail transformation engagement scope, cadence, and deliverables.",
        type="project-doc",
        status="active",
        domain="engagement",
        created="2026-05-10",
        updated="2026-05-20",
    )
    _write(
        dest,
        "20-client/northwind-stakeholder-map.md",
        "Primary sponsor: CIO. Working group leads listed in the meeting notes.",
        title="Northwind stakeholder map",
        summary="Stakeholder map for the Northwind Retail client including sponsors and working group leads.",
        type="stakeholder",
        status="active",
        domain="client",
        created="2026-05-12",
        updated="2026-05-18",
    )
    _write(
        dest,
        "60-decisions/adr-0001-discovery-approach.md",
        "## Status\nSuperseded by [ADR-0002](adr-0002-phased-rollout.md).\n\n"
        "## Decision\nRun a single big-bang discovery workshop.",
        title="ADR-0001 Discovery approach",
        summary="Original decision to run a single discovery workshop before phased delivery was adopted.",
        type="adr",
        status="superseded",
        domain="engagement",
        created="2026-05-15",
        updated="2026-06-01",
    )
    _write(
        dest,
        "60-decisions/adr-0002-phased-rollout.md",
        "## Status\nAccepted. Supersedes [ADR-0001](adr-0001-discovery-approach.md).\n\n"
        "## Decision\nUse phased discovery waves by business unit.",
        title="ADR-0002 Phased rollout",
        summary="Accepted decision to run phased discovery waves instead of a single monolithic workshop.",
        type="adr",
        status="active",
        domain="engagement",
        created="2026-06-01",
        updated="2026-06-01",
    )
    _write(
        dest,
        "20-client/governance-finding-data-residency.md",
        "Finding: legacy CRM exports include EU customer PII outside the agreed residency boundary.",
        title="Data residency finding",
        summary="Governance finding on EU customer PII appearing outside the agreed data residency boundary.",
        type="governance-finding",
        status="in-review",
        domain="client",
        created="2026-06-08",
        updated="2026-06-08",
    )
    _write(
        dest,
        "70-meetings/2026-06-10-steering-committee.md",
        "Steering committee reviewed ADR-0002 and open residency conflicts in client interviews.",
        title="Steering committee 2026-06-10",
        summary="Steering committee meeting reviewing phased rollout and conflicting residency interview claims.",
        type="meeting",
        status="done",
        domain="engagement",
        created="2026-06-10",
        updated="2026-06-10",
    )
    _write(
        dest,
        "71-log/2026-06-11-client-synthesis.md",
        "Synthesized interview sources; residency contradiction flagged for partner review.",
        title="Client synthesis log",
        summary="Log entry for synthesizing client interview sources with a flagged residency contradiction.",
        type="log",
        status="done",
        domain="engagement",
        created="2026-06-11",
        updated="2026-06-11",
    )
    _write(
        dest,
        "05-sources/interview-cio-transcript.md",
        "CIO states all customer data resides in **EU-West** regions only.",
        title="CIO interview transcript",
        summary="Source transcript where the CIO claims all customer data resides in EU-West regions.",
        type="source",
        status="active",
        domain="client",
        created="2026-06-05",
        updated="2026-07-08",
    )
    _write(
        dest,
        "05-sources/interview-ops-transcript.md",
        "Operations lead reports nightly backups copied to **US-East** for analytics.",
        title="Operations interview transcript",
        summary="Source transcript where operations reports backups copied to US-East, conflicting with CIO claim.",
        type="source",
        status="active",
        domain="client",
        created="2026-06-06",
        updated="2026-06-06",
    )
    _write(
        dest,
        "85-synthesis/concept/data-residency.md",
        "## Open questions and contradictions\n"
        "CIO claims EU-only residency; operations cites US-East backups. Unresolved conflict.",
        title="Data residency posture",
        summary="Synthesized concept page with unresolved data residency contradiction across interview sources.",
        type="concept",
        status="active",
        domain="client",
        synthesis="generated",
        review="needed",
        sources=["05-sources/interview-cio-transcript.md", "05-sources/interview-ops-transcript.md"],
        generated_at="2026-06-07",
        created="2026-06-07",
        updated="2026-06-07",
    )
    _write(
        dest,
        "85-synthesis/entity/northwind-cio.md",
        "Executive sponsor for the transformation program.",
        title="Northwind CIO",
        summary="Synthesized entity page for the Northwind CIO with stale source linkage pending refresh.",
        type="entity",
        status="active",
        domain="client",
        synthesis="generated",
        review="needed",
        sources=["05-sources/interview-cio-transcript.md"],
        generated_at="2026-06-01",
        created="2026-06-01",
        updated="2026-06-01",
    )
    _finalize(dest)


def build_research_project(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    scaffold_auxmem(
        dest,
        name="cell-count-ml",
        domains=["10-literature=literature", "20-experiments=experiments"],
    )

    _write(
        dest,
        "10-literature/research-questions.md",
        "Primary question: can lightweight microscopy models generalize across cell lines?",
        title="Research questions",
        summary="Research questions for the cell-count machine learning project and literature review scope.",
        type="project-doc",
        status="active",
        domain="literature",
        created="2026-04-01",
        updated="2026-04-15",
    )
    _write(
        dest,
        "20-experiments/exp-014-baseline.md",
        "Baseline run on dataset A. Linked to sources in `05-sources/`.",
        title="Experiment 014 baseline",
        summary="Baseline experiment record for dataset A with links to captured literature sources.",
        type="project-doc",
        status="active",
        domain="experiments",
        created="2026-05-20",
        updated="2026-05-25",
    )
    _write(
        dest,
        "60-decisions/adr-0001-labeling-protocol.md",
        "## Status\nSuperseded by [ADR-0002](adr-0002-active-learning.md).\n\n"
        "## Decision\nUse fully manual bounding-box labeling.",
        title="ADR-0001 Labeling protocol",
        summary="Original decision to rely on fully manual bounding-box labeling for training data.",
        type="adr",
        status="superseded",
        domain="experiments",
        created="2026-04-20",
        updated="2026-05-01",
    )
    _write(
        dest,
        "60-decisions/adr-0002-active-learning.md",
        "## Status\nAccepted. Supersedes [ADR-0001](adr-0001-labeling-protocol.md).\n\n"
        "## Decision\nAdopt active learning with reviewer gates.",
        title="ADR-0002 Active learning",
        summary="Accepted decision to adopt active learning with reviewer gates instead of fully manual labeling.",
        type="adr",
        status="active",
        domain="experiments",
        created="2026-05-01",
        updated="2026-05-01",
    )
    _write(
        dest,
        "70-meetings/2026-05-22-lab-standup.md",
        "Reviewed conflicting accuracy claims in two papers; left synthesis stale pending PI review.",
        title="Lab standup 2026-05-22",
        summary="Lab standup covering conflicting paper accuracy claims and stale synthesis follow-up.",
        type="meeting",
        status="done",
        domain="experiments",
        created="2026-05-22",
        updated="2026-05-22",
    )
    _write(
        dest,
        "71-log/2026-05-23-literature-synthesis.md",
        "Synthesized paper summaries; accuracy contradiction documented, not resolved.",
        title="Literature synthesis log",
        summary="Log entry for literature synthesis with documented accuracy contradiction across papers.",
        type="log",
        status="done",
        domain="literature",
        created="2026-05-23",
        updated="2026-05-23",
    )
    _write(
        dest,
        "05-sources/paper-microcount-2024.md",
        "MicroCount reports **92%** accuracy on dataset A.",
        title="MicroCount 2024 paper",
        summary="Source summary of MicroCount 2024 paper reporting ninety-two percent accuracy on dataset A.",
        type="source",
        status="active",
        domain="literature",
        created="2026-05-01",
        updated="2026-07-05",
    )
    _write(
        dest,
        "05-sources/paper-cellnet-2023.md",
        "CellNet reports **88%** accuracy on the same dataset A protocol.",
        title="CellNet 2023 paper",
        summary="Source summary of CellNet 2023 paper reporting eighty-eight percent accuracy on dataset A.",
        type="source",
        status="active",
        domain="literature",
        created="2026-05-02",
        updated="2026-05-02",
    )
    _write(
        dest,
        "85-synthesis/concept/dataset-a-accuracy.md",
        "## Open questions and contradictions\n"
        "MicroCount: 92%. CellNet: 88%. Papers use slightly different splits; unresolved.",
        title="Dataset A accuracy claims",
        summary="Synthesized concept page documenting conflicting accuracy claims across literature sources.",
        type="concept",
        status="active",
        domain="literature",
        synthesis="generated",
        review="needed",
        sources=["05-sources/paper-microcount-2024.md", "05-sources/paper-cellnet-2023.md"],
        generated_at="2026-05-10",
        created="2026-05-10",
        updated="2026-05-10",
    )
    _write(
        dest,
        "85-synthesis/entity/microcount-model.md",
        "Lightweight counting model from the MicroCount paper.",
        title="MicroCount model",
        summary="Synthesized entity page for the MicroCount model with stale linkage to updated paper source.",
        type="entity",
        status="active",
        domain="literature",
        synthesis="generated",
        review="needed",
        sources=["05-sources/paper-microcount-2024.md"],
        generated_at="2026-05-01",
        created="2026-05-01",
        updated="2026-05-01",
    )
    _finalize(dest)


BUILDERS = {
    "software-project": build_software_project,
    "consulting-engagement": build_consulting_engagement,
    "research-project": build_research_project,
}


def main() -> int:
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    for name in REFERENCE_NAMES:
        dest = EXAMPLES / name
        print(f"building {dest}...")
        BUILDERS[name](dest)
        cfg = json.loads((dest / ".scripts/auxmem.config.json").read_text(encoding="utf-8"))
        print(f"  ok: {cfg['name']} domains={list(cfg['domains'].keys())}")
    print("reference auxmems materialized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
