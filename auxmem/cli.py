"""auxmem command-line interface.

Subcommands:
  auxmem new         create an auxmem (interactive wizard, or flag-driven)
  auxmem seed        stage 1 of seeding: normalize a provider export to staging
  auxmem import-obsidian   import an existing Obsidian vault into an auxmem
  auxmem doctor      check an auxmem: validate + MOC freshness
"""

import argparse
import sys
from pathlib import Path

from . import scaffold, wizard, importers, upgrade as upgrade_mod

EPILOG = """
where to run commands
  All auxmem subcommands run from any directory. You do not need to cd into an
  auxmem folder first. When a command needs an existing auxmem, pass its path as
  an argument (or as --dest).

  Setup (no auxmem yet):
    new                 create an auxmem at the path you choose (shared folders only);
                        run the setup-domains skill inside the folder to add subjects

  Existing auxmem (pass the folder path):
    doctor PATH         validate and refresh navigation maps
    upgrade PATH        migrate auxmem tooling to the current template
    import-obsidian … --dest PATH   import notes into that auxmem

  Outside any auxmem (import prep):
    seed EXPORT         write a staging corpus (default ./seed-staging); stage 2
                        is an agent step run from inside the target auxmem

  Inside the auxmem (not auxmem subcommands):
    ./bootstrap.sh, agent skills, python3 .scripts/validate_auxmem.py — see
    AGENTS.md for day-to-day work.
"""


def cmd_upgrade(args):
    try:
        result = upgrade_mod.upgrade(args.dest, force=args.force)
    except upgrade_mod.UpgradeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if result["status"] == "up-to-date":
        print(f"already at template version {result['version']}. Use --force to re-apply.")
        return 0
    print(f"upgraded {args.dest}: {result['from']} -> {result['to']}")
    for c in result["changes"]:
        print(f"  {c}")
    print(f"\nbackup: {result['backup']}")
    print(f"report: {Path(args.dest) / '00-inbox'} (upgrade-report-*.md)")
    if result["conflicts"]:
        print(f"\n{len(result['conflicts'])} file(s) need manual review (see report).")
    if not result["valid"]:
        print("\nWARNING: validation did not pass after upgrade:")
        print(result["validation"])
        return 2
    print("\nvalidation clean.")
    return 0


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
        if domains:
            print("next: set your git remote and push (see the auxmem README).")
        else:
            print("next: point your agent at the auxmem and run the setup-domains skill.")
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
    return rc


def cmd_import_obsidian(args):
    try:
        if args.no_pipeline:
            rc, out, err = importers.migrate_obsidian_single(
                args.src, args.dest, map_file=args.map, dry_run=args.dry_run)
        else:
            rc, out, err = importers.migrate_obsidian_pipeline(
                args.src, args.dest, args.export_tmp, map_file=args.map, dry_run=args.dry_run)
    except importers.ImportError_ as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(out or err)
    if rc == 0 and not args.dry_run:
        print(f"\nReview {Path(args.dest) / '00-inbox' / 'migration-report.md'} before committing.")
    return rc


def cmd_doctor(args):
    try:
        rc, out, err = importers.validate_and_moc(args.dest)
    except importers.ImportError_ as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(out or err)
    return rc


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
            "--path. Add subject domains afterward with the setup-domains skill, or "
            "pass --domain when the layout is already known."
        ),
    )
    n.add_argument("--name")
    n.add_argument("--path")
    n.add_argument("--domain", action="append", metavar="NN-folder=slug",
                   help="optional; repeatable — omit to defer domains to setup-domains")
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

    o = sub.add_parser(
        "import-obsidian",
        help="import Obsidian notes into an existing auxmem",
        description=(
            "Import an Obsidian vault into an existing auxmem. Run from anywhere; "
            "pass the auxmem folder path as --dest."
        ),
    )
    o.add_argument("src", help="path to the existing Obsidian vault")
    o.add_argument("--dest", required=True, metavar="AUXMEM",
                   help="path to the target auxmem (must already exist)")
    o.add_argument("--map", help="folder map JSON")
    o.add_argument("--export-tmp", default="/tmp/auxmem-obsidian-export")
    o.add_argument("--no-pipeline", action="store_true",
                   help="use the single-script fallback instead of obsidian-export")
    o.add_argument("--dry-run", action="store_true")
    o.set_defaults(func=cmd_import_obsidian)

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
