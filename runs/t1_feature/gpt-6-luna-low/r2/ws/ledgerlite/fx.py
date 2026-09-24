"""Foreign exchange rate loading and conversion."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import Transaction, to_money


class MissingRateError(ValueError):
    """No sufficiently recent rate is available for a transaction."""


def load_rates(path: str | Path) -> dict[str, dict[date, Decimal]]:
    rates: dict[str, dict[date, Decimal]] = defaultdict(dict)
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or [h.strip().lower() for h in reader.fieldnames] != ["date", "currency", "rate"]:
            raise ValueError("rate CSV header must be date,currency,rate")
        for row in reader:
            day = date.fromisoformat(row["date"].strip())
            currency = row["currency"].strip().upper()
            try:
                rate = Decimal(row["rate"].strip())
            except InvalidOperation as exc:
                raise ValueError(f"bad rate: {row['rate']!r}") from exc
            rates[currency][day] = rate
    return dict(rates)


def convert(transactions: list[Transaction], rates: dict, base: str = "EUR") -> list[Transaction]:
    base = base.upper()
    for tx in transactions:
        currency = tx.currency.upper()
        tx.currency = currency
        tx.original_amount = tx.amount
        if currency == base:
            rate = Decimal("1")
        else:
            currency_rates = rates.get(currency, {})
            eligible = [day for day in currency_rates if day <= tx.date and (tx.date - day).days <= 7]
            if not eligible:
                raise MissingRateError(f"missing exchange rate for {currency} on {tx.date.isoformat()}")
            rate = currency_rates[max(eligible)]
        tx.amount = to_money(tx.original_amount * rate)
    return transactions
