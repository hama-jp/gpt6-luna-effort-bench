"""Command line entry point.

    python -m ledgerlite report --rules rules.txt --month 2026-03 a.csv b.csv
"""
from __future__ import annotations

import argparse
import sys

from .categorize import categorize, load_rules
from .dedupe import dedupe
from .fx import MissingRateError, convert, load_rates
from .importer import read_statement
from .report import format_summary, monthly_summary


def load_all(paths: list[str], rules_path: str | None, base: str = "EUR"):
    txs = []
    for p in paths:
        txs.extend(read_statement(p, base=base))
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
    rp.add_argument("--base", default="EUR", help="reporting currency code (default: EUR)")
    rp.add_argument("--rates", help="CSV exchange rates file")
    rp.add_argument("files", nargs="+")
    args = ap.parse_args(argv)

    if args.cmd == "report":
        year, month = (int(x) for x in args.month.split("-"))
        base = args.base.upper()
        txs = load_all(args.files, args.rules, base=base)
        if args.rates is None and any(tx.currency != base for tx in txs):
            print("error: --rates is required when transactions use currencies other than --base", file=sys.stderr)
            return 2
        try:
            rates = load_rates(args.rates) if args.rates is not None else {}
            convert(txs, rates, base=base)
        except MissingRateError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(format_summary(monthly_summary(txs, year, month, base=base)))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
