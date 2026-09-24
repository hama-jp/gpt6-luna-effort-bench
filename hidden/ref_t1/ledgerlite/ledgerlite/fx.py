"""Currency conversion."""
from __future__ import annotations

import csv
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from .models import Transaction, to_money

MAX_AGE = timedelta(days=7)


class MissingRateError(ValueError):
    pass


def load_rates(path: str | Path) -> dict[str, list[tuple[date, Decimal]]]:
    rates: dict[str, list[tuple[date, Decimal]]] = {}
    with Path(path).open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rates.setdefault(row["currency"].strip().upper(), []).append(
                (date.fromisoformat(row["date"].strip()), Decimal(row["rate"].strip())))
    for v in rates.values():
        v.sort()
    return rates


def rate_for(rates, currency: str, day: date) -> Decimal:
    best = None
    for d, r in rates.get(currency, []):
        if d <= day and day - d <= MAX_AGE:
            best = r
    if best is None:
        raise MissingRateError(f"no {currency} rate for {day.isoformat()}")
    return best


def convert(transactions: list[Transaction], rates, base: str = "EUR") -> list[Transaction]:
    base = base.upper()
    for t in transactions:
        rate = Decimal(1) if t.currency == base else rate_for(rates, t.currency, t.date)
        t.original_amount = t.amount
        t.amount = to_money(t.original_amount * rate)
    return transactions
