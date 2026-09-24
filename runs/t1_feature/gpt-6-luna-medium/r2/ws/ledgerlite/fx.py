"""Foreign exchange rate loading and conversion."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from .models import Transaction, to_money


class MissingRateError(ValueError):
    """No sufficiently recent rate is available for a transaction."""


def load_rates(path: str | Path) -> dict[str, list[tuple[date, Decimal]]]:
    rates: dict[str, list[tuple[date, Decimal]]] = defaultdict(list)
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or [x.strip().lower() for x in reader.fieldnames] != ["date", "currency", "rate"]:
            raise ValueError("rates CSV must have header date,currency,rate")
        for row in reader:
            rates[row["currency"].strip().upper()].append(
                (date.fromisoformat(row["date"].strip()), Decimal(row["rate"].strip()))
            )
    for entries in rates.values():
        entries.sort(key=lambda x: x[0])
    return dict(rates)


def convert(transactions: list[Transaction], rates: dict, base: str = "EUR") -> list[Transaction]:
    base = base.upper()
    for tx in transactions:
        original = tx.amount
        tx.original_amount = original
        if tx.currency.upper() == base:
            tx.amount = to_money(original)
            continue
        candidates = [r for d, r in rates.get(tx.currency.upper(), []) if tx.date - timedelta(days=7) <= d <= tx.date]
        if not candidates:
            raise MissingRateError(f"missing rate for {tx.currency.upper()} on {tx.date.isoformat()}")
        tx.amount = to_money(original * candidates[-1])
    return transactions
