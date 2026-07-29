from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import __version__
from .core import candidate_diff, evaluate, heal, health, load_cases, promote, rollback, scan
from .store import Store


def emit(payload: Any) -> None:
    print(json.dumps(payload, indent=2))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="skillkeeper", description="Observe, test, stage, and improve Agent Skills.")
    root.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    root.add_argument("--state-dir", type=Path, default=Path(".skillkeeper"))
    commands = root.add_subparsers(dest="command", required=True)

    inventory = commands.add_parser("scan", help="Index skill roots and discover dependencies")
    inventory.add_argument("roots", nargs="+", type=Path)

    listed = commands.add_parser("inventory", help="Show the current indexed inventory")

    check = commands.add_parser("evaluate", help="Run replay requirements against one skill")
    check.add_argument("skill", type=Path)
    check.add_argument("cases", nargs="+", type=Path)
    check.add_argument("--suite", default="replay")

    health_cmd = commands.add_parser("health", help="Calculate a skill health score")
    health_cmd.add_argument("skill", type=Path)
    health_cmd.add_argument("cases", nargs="+", type=Path)

    heal_cmd = commands.add_parser("heal", help="Generate and gate a staged candidate")
    heal_cmd.add_argument("skill", type=Path)
    heal_cmd.add_argument("--train", nargs="+", required=True, type=Path)
    heal_cmd.add_argument("--holdout", nargs="+", required=True, type=Path)
    heal_cmd.add_argument("--minimum-train", type=float, default=1.0)
    heal_cmd.add_argument("--minimum-holdout", type=float, default=0.8)
    heal_cmd.add_argument("--max-repairs", type=int, default=12)

    diff_cmd = commands.add_parser("diff", help="Show a staged candidate diff")
    diff_cmd.add_argument("candidate_id")

    promote_cmd = commands.add_parser("promote", help="Promote one passing staged candidate")
    promote_cmd.add_argument("candidate_id")

    rollback_cmd = commands.add_parser("rollback", help="Restore a named skill backup")
    rollback_cmd.add_argument("skill", type=Path)
    rollback_cmd.add_argument("backup", type=Path)

    events = commands.add_parser("events", help="Show the recent audit trail")
    events.add_argument("--limit", type=int, default=20)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    store = Store(args.state_dir)
    try:
        if args.command == "scan":
            emit(scan(args.roots, store))
        elif args.command == "inventory":
            emit(store.inventory())
        elif args.command == "evaluate":
            report = evaluate(args.skill, load_cases(args.cases), args.suite)
            store.record_evaluation(report)
            emit(report)
        elif args.command == "health":
            emit(health(args.skill, load_cases(args.cases)))
        elif args.command == "heal":
            emit(
                heal(
                    args.skill,
                    load_cases(args.train),
                    load_cases(args.holdout),
                    store,
                    minimum_train=args.minimum_train,
                    minimum_holdout=args.minimum_holdout,
                    max_repairs=args.max_repairs,
                )
            )
        elif args.command == "diff":
            print(candidate_diff(store, args.candidate_id))
        elif args.command == "promote":
            emit(promote(store, args.candidate_id))
        elif args.command == "rollback":
            emit(rollback(store, args.skill, args.backup))
        elif args.command == "events":
            emit(store.recent_events(args.limit))
        return 0
    except ValueError as error:
        parser().error(str(error))
        return 2
    finally:
        store.close()
