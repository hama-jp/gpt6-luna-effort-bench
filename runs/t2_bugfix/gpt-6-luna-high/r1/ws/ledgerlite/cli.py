"""Command line entry point.

    python -m ledgerlite report --rules rules.txt --month 2026-03 a.csv b.csv
"""
from __future__ import annotations

import argparse
import sys

from .categorize import categorize, load_rules
from .dedupe import dedupe
from .importer import read_statement
from .report import format_summary, monthly_summary


def load_all(paths: list[str], rules_path: str | None):
    txs = []
    for p in paths:
        txs.extend(read_statement(p))
    txs = dedupe(txs)
    if rules_path:
        categorize(txs, load_rules(rules_path))
    return txs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ledgerlite")
    sub = ap.add_subparsers(dest="cmd", required=True)
    rp = sub.add_parser("report", help="monthly summary")
    rp.add_argument("--rules")
    rp.add_argument("--month", required=True, help="YYYY-MM")
    rp.add_argument("files", nargs="+")
    args = ap.parse_args(argv)

    if args.cmd == "report":
        year, month = (int(x) for x in args.month.split("-"))
        txs = load_all(args.files, args.rules)
        print(format_summary(monthly_summary(txs, year, month)))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
