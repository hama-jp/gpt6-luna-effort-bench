"""Foreign exchange rate loading and transaction conversion."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from decimal import Decimal

from .models import Transaction, to_money


class MissingRateError(ValueError):
    """No sufficiently recent exchange rate is available."""


def load_rates(path: str | Path) -> dict[str, dict[date, Decimal]]:
    rates: dict[str, dict[date, Decimal]] = {}
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or not {"date", "currency", "rate"}.issubset(reader.fieldnames):
            raise ValueError("rates CSV must have date,currency,rate headers")
        for row in reader:
            day = date.fromisoformat(row["date"].strip())
            currency = row["currency"].strip().upper()
            rate = Decimal(row["rate"].strip())
            rates.setdefault(currency, {})[day] = rate
    return rates


def convert(transactions: list[Transaction], rates: dict, base: str = "EUR") -> list[Transaction]:
    base = base.upper()
    for tx in transactions:
        tx.currency = tx.currency.upper()
        tx.original_amount = tx.amount
        if tx.currency.upper() == base:
            tx.amount = to_money(tx.original_amount)
            continue
        available = rates.get(tx.currency.upper(), {})
        prior = [day for day in available if day <= tx.date]
        rate_day = max(prior) if prior else None
        if rate_day is None or (tx.date - rate_day).days > 7:
            raise MissingRateError(f"missing rate for {tx.currency.upper()} on {tx.date.isoformat()}")
        tx.amount = to_money(tx.original_amount * available[rate_day])
    return transactions
