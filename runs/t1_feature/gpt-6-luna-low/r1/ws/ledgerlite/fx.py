"""Foreign exchange rate loading and conversion."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import Transaction, to_money


class MissingRateError(ValueError):
    """No sufficiently recent rate exists for a transaction."""


def load_rates(path: str | Path) -> dict[str, dict[date, Decimal]]:
    rates: dict[str, dict[date, Decimal]] = defaultdict(dict)
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or [f.strip().lower() for f in reader.fieldnames] != ["date", "currency", "rate"]:
            raise ValueError("rates CSV must have header date,currency,rate")
        for row in reader:
            try:
                day = date.fromisoformat(row["date"].strip())
                code = row["currency"].strip().upper()
                rate = Decimal(row["rate"].strip())
            except (ValueError, AttributeError, InvalidOperation) as exc:
                raise ValueError(f"invalid rate row: {row}") from exc
            rates[code][day] = rate
    return dict(rates)


def _rate_on_or_before(rates, currency: str, day: date) -> Decimal:
    dated = rates.get(currency, {})
    candidates = [d for d in dated if 0 <= (day - d).days <= 7]
    if not candidates:
        raise MissingRateError(f"missing rate for {currency} on {day.isoformat()}")
    return dated[max(candidates)]


def convert(transactions: list[Transaction], rates, base: str = "EUR") -> list[Transaction]:
    base = base.upper()
    for tx in transactions:
        tx.original_amount = tx.amount
        if tx.currency.upper() == base:
            tx.currency = base
            continue
        rate = _rate_on_or_before(rates, tx.currency.upper(), tx.date)
        tx.amount = to_money(tx.original_amount * rate)
    return transactions
