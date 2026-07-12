"""auxmem command-line interface.

Subcommands:
  auxmem new         create an auxmem (interactive wizard, or flag-driven)
  auxmem seed        stage 1 of seeding: normalize a provider export to staging
  auxmem doctor      check an auxmem: validate + MOC freshness
  auxmem check       read-only conformance check (CI-safe)
"""

import argparse
import sys
from pathlib import Path

from . import importers, scaffold, wizard
from . import upgrade as upgrade_mod
from .exit_codes import NON_CONFORMANT, OK, OPERATION_FAILED

EPILOG = """
where to run commands
  All auxmem subcommands run from any directory. You do not need to cd into an
  auxmem folder first. When a command needs an existing auxmem, pass its path as
  an argument (or as --dest).

  Setup (no auxmem yet):
    new                 create an auxmem at the path you choose (shared folders only);
                        run the auxmem-init skill inside the folder to finish setup

  Existing auxmem (pass the folder path):
    check PATH          read-only validation + MOC freshness (for CI)
    doctor PATH         validate and refresh navigation maps
    upgrade PATH        migrate auxmem tooling to the current template

  Outside any auxmem (import prep):
    seed EXPORT         write a staging corpus (default ./seed-staging); stage 2
                        is an agent step run from inside the target auxmem

  Inside the auxmem (not auxmem subcommands):
    ./bootstrap.sh, agent skills, python3 .scripts/validate_auxmem.py — see
    AGENTS.md for day-to-day work.
"""


def cmd_upgrade(args):
    try:
        result = upgrade_mod.upgrade(args.dest, force=args.force, dry_run=args.dry_run)
    except upgrade_mod.UpgradeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if result["status"] == "up-to-date":
        print(f"already at template version {result['version']}. Use --force to re-apply.")
        return 0
    if result["status"] == "dry-run":
        print(f"dry-run: {result['from']} -> {result['to']}")
        if result.get("deprecated"):
            print("\nDeprecated (left in place):")
            for item in result["deprecated"]:
                print(f"  {item}")
        print("\nPlanned changes:")
        for change in result["changes"]:
            print(f"  {change}")
        if result["conflicts"]:
            print(f"\nLikely conflicts ({len(result['conflicts'])}):")
            for rel in result["conflicts"]:
                print(f"  {rel}")
        expected = result.get("post_validation_expected")
        if expected is True:
            print("\nPost-upgrade validation: expected to pass")
        elif expected is False:
            print("\nPost-upgrade validation: expected to FAIL")
            if result.get("post_detail"):
                print(result["post_detail"])
        print("\n(dry-run made no changes)")
        return OK
    if result["status"] == "failed":
        print(f"upgrade failed and was rolled back: {args.dest}")
        if result.get("post_phase"):
            print(f"{result['post_phase']} failed:")
            print(result.get("post_detail", ""))
        return result.get("post_exit_code", OPERATION_FAILED)
    print(f"upgraded {args.dest}: {result['from']} -> {result['to']}")
    for c in result["changes"]:
        print(f"  {c}")
    print(f"\nbackup: {result['backup']}")
    print(f"report: {Path(args.dest) / '00-inbox'} (upgrade-report-*.md)")
    if result["conflicts"]:
        print(f"\n{len(result['conflicts'])} file(s) need manual review (see report).")
    post_code = result.get("post_exit_code", OK)
    if post_code == OPERATION_FAILED:
        print(f"\n{result['post_phase']} failed after upgrade:")
        print(result["post_detail"])
        return OPERATION_FAILED
    if post_code == NON_CONFORMANT:
        print("\nValidation did not pass after upgrade:")
        print(result["post_detail"])
        return NON_CONFORMANT
    print("\nvalidation clean.")
    return OK


def cmd_new(args):
    if args.name and args.path:
        try:
            domains = scaffold.parse_domains(args.domain) if args.domain else {}
            result = scaffold.scaffold(args.name, args.path, domains,
                                       run_bootstrap=not args.no_bootstrap)
        except scaffold.ScaffoldError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"created {result['dest']}")
        print("next: point your agent at the auxmem and run the auxmem-init skill.")
        if domains:
            print("      (domains are pre-configured; init will confirm and finish setup)")
        else:
            print("      (init will interview you and set up subject domains)")
        return 0
    # any flags missing -> interactive
    try:
        wizard.run()
    except scaffold.ScaffoldError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ncancelled.")
        return 130
    return 0


def cmd_seed(args):
    rc, out, err = importers.extract_export(
        args.export_file, args.staging, provider=args.provider,
        since=args.since, min_messages=args.min_messages)
    print(out or err)
    if rc == 0:
        print("\nStage 2: distill the staging corpus into notes with an agent.")
        print("Run your CLI agent from the target auxmem and point it at:")
        print(f"  {importers.IMPORTERS / 'distill-seeds.md'}")
    return rc if rc != 0 else OK


def cmd_doctor(args):
    try:
        exit_code, message = importers.validate_and_moc(args.dest)
    except importers.ImportError_ as e:
        print(f"error: {e}", file=sys.stderr)
        return OPERATION_FAILED
    print(message)
    return exit_code


def cmd_check(args):
    try:
        exit_code, message = importers.check_conformance(
            args.dest, manifest=args.manifest, git=args.git
        )
    except importers.ImportError_ as e:
        print(f"error: {e}", file=sys.stderr)
        return OPERATION_FAILED
    print(message)
    return exit_code


def build_parser():
    p = argparse.ArgumentParser(
        prog="auxmem",
        description=(
            "AuxMem Manager — create and maintain auxmems (governed markdown memory "
            "for AI agents). Run from any directory; pass an auxmem path when a "
            "command needs an existing folder."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(
        dest="cmd",
        title="commands",
        metavar="COMMAND",
        help="run auxmem COMMAND --help for details",
    )

    n = sub.add_parser(
        "new",
        help="create a new auxmem (no existing auxmem needed)",
        description=(
            "Create a new auxmem with shared folders only. Run from anywhere; writes to "
            "--path. Finish setup with the auxmem-init skill, or pass --domain when the "
            "layout is already known."
        ),
    )
    n.add_argument("--name")
    n.add_argument("--path")
    n.add_argument("--domain", action="append", metavar="NN-folder=slug",
                   help="optional; repeatable — omit to defer domains to auxmem-init")
    n.add_argument("--no-bootstrap", action="store_true", help="skip folder/hook/validate setup")
    n.set_defaults(func=cmd_new)

    s = sub.add_parser(
        "seed",
        help="normalize an export to staging (outside any auxmem)",
        description=(
            "Stage 1 of seeding: normalize a provider export into a staging folder "
            "(default ./seed-staging). Does not modify an auxmem. Stage 2 (distill into "
            "notes) is an agent step run from inside the target auxmem."
        ),
    )
    s.add_argument("export_file")
    s.add_argument("--staging", default="./seed-staging",
                   help="output folder, usually outside the auxmem (default: ./seed-staging)")
    s.add_argument("--provider", choices=["claude", "chatgpt", "gemini"])
    s.add_argument("--since")
    s.add_argument("--min-messages", type=int)
    s.set_defaults(func=cmd_seed)

    d = sub.add_parser(
        "doctor",
        help="validate an existing auxmem and refresh its MOCs",
        description=(
            "Validate an auxmem and regenerate its navigation maps. Run from anywhere; "
            "pass the auxmem path as the argument."
        ),
    )
    d.add_argument("dest", metavar="AUXMEM", help="path to the auxmem folder")
    d.set_defaults(func=cmd_doctor)

    c = sub.add_parser(
        "check",
        help="read-only conformance check for an existing auxmem",
        description=(
            "Validate an auxmem and verify MOC freshness without modifying any files. "
            "Appropriate for CI. Use doctor to regenerate stale MOCs."
        ),
    )
    c.add_argument("dest", metavar="AUXMEM", help="path to the auxmem folder")
    c.add_argument(
        "--manifest",
        action="store_true",
        help="also verify managed tooling files listed in .auxmem/manifest.json",
    )
    c.add_argument(
        "--git",
        action="store_true",
        help="also require a clean git working tree",
    )
    c.set_defaults(func=cmd_check)

    u = sub.add_parser(
        "upgrade",
        help="migrate an existing auxmem to the current template",
        description=(
            "Upgrade auxmem tooling to the current template version. Run from anywhere; "
            "pass the auxmem folder path as the argument. Never touches your notes."
        ),
    )
    u.add_argument("dest", metavar="AUXMEM", help="path to the auxmem to upgrade")
    u.add_argument("--force", action="store_true", help="re-apply even if already current")
    u.add_argument(
        "--dry-run",
        action="store_true",
        help="report planned changes without modifying the auxmem",
    )
    u.set_defaults(func=cmd_upgrade)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
