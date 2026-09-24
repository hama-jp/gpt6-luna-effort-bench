"""Foreign exchange rate loading and transaction conversion."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from .models import Transaction, to_money


class MissingRateError(ValueError):
    """No sufficiently recent rate is available for a transaction."""


def load_rates(path: str | Path) -> dict[str, list[tuple[date, Decimal]]]:
    """Load CSV rates, grouped by upper-case currency code."""
    rates: dict[str, list[tuple[date, Decimal]]] = defaultdict(list)
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or [x.strip().lower() for x in reader.fieldnames] != ["date", "currency", "rate"]:
            raise ValueError("rate file must have header date,currency,rate")
        for row in reader:
            currency = row["currency"].strip().upper()
            rates[currency].append((date.fromisoformat(row["date"].strip()), Decimal(row["rate"].strip())))
    for entries in rates.values():
        entries.sort(key=lambda entry: entry[0])
    return dict(rates)


def convert(transactions: list[Transaction], rates: dict, base: str = "EUR") -> list[Transaction]:
    """Convert transactions in place into ``base`` while retaining source currency."""
    base = base.upper()
    for tx in transactions:
        original = tx.amount
        tx.original_amount = original
        if tx.currency.upper() == base:
            tx.amount = to_money(original)
            continue
        dated_rates = rates.get(tx.currency.upper(), [])
        eligible = [(day, rate) for day, rate in dated_rates if day <= tx.date and (tx.date - day).days <= 7]
        if not eligible:
            raise MissingRateError(f"missing rate for {tx.currency.upper()} on {tx.date.isoformat()}")
        _, rate = max(eligible, key=lambda entry: entry[0])
        tx.amount = to_money(original * rate)
    return transactions
