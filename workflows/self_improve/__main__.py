"""Explicit CLI for recording real checks and exporting portable evidence."""
import argparse
import json
import sys
from pathlib import Path
from capabilities.exploration.ledger import Ledger
from capabilities.exploration.export import portable_records
from runtime.runner import evaluate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--db", required=True)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run")
    run.add_argument("--id", required=True)
    run.add_argument("--parent")
    run.add_argument("--round", type=int, required=True)
    run.add_argument("--phase", choices=("before", "after", "baseline", "final"), required=True)
    run.add_argument("--hypothesis", required=True)
    run.add_argument("--timeout", type=float, default=30)
    run.add_argument("command", nargs=argparse.REMAINDER)
    export = sub.add_parser("export")
    export.add_argument("--out", required=True)
    sub.add_parser("verify")
    args = parser.parse_args()
    ledger = Ledger(args.db)
    try:
        if args.action == "run":
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            if not command:
                parser.error("explicit evaluator command is required")
            record = {"id": args.id, "parent": args.parent, "round": args.round,
                      "phase": args.phase, "hypothesis": args.hypothesis,
                      "evaluation": evaluate(args.root, command, args.timeout)}
            ledger.append(record)
            print(json.dumps({"id": record["id"], "status": record["evaluation"]["status"],
                              "exit_code": record["evaluation"]["exit_code"]}))
            return 0 if record["evaluation"]["status"] == "pass" else 1
        elif args.action == "verify":
            print(json.dumps(ledger.verify()))
        else:
            ledger.verify()
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(portable_records(ledger.records()), indent=2, ensure_ascii=False) + "\n")
    finally:
        ledger.close()


if __name__ == "__main__":
    raise SystemExit(main())
