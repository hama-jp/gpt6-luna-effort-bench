"""Load dated exchange rates and convert transactions to a base currency."""
from __future__ import annotations

import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import Transaction, to_money


class MissingRateError(ValueError):
    """No sufficiently recent rate is available for a transaction."""


Rates = dict[str, dict[date, Decimal]]


def load_rates(path: str | Path) -> Rates:
    """Read a CSV with ``date,currency,rate`` columns."""
    rates: Rates = {}
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = [field.strip().lower() for field in (reader.fieldnames or [])]
        if fields != ["date", "currency", "rate"]:
            raise ValueError("rates CSV must have header date,currency,rate")
        for lineno, row in enumerate(reader, start=2):
            try:
                rate_date = date.fromisoformat(row["date"].strip())
                currency = row["currency"].strip().upper()
                rate = Decimal(row["rate"].strip())
            except (AttributeError, KeyError, TypeError, ValueError, InvalidOperation) as exc:
                raise ValueError(f"rates CSV line {lineno}: invalid date, currency, or rate") from exc
            rates.setdefault(currency, {})[rate_date] = rate
    return rates


def convert(transactions: list[Transaction], rates: Rates, base: str = "EUR") -> list[Transaction]:
    """Convert transactions in place and return the same list."""
    base = base.strip().upper()
    conversions: list[tuple[Transaction, Decimal, Decimal]] = []
    for tx in transactions:
        original_amount = tx.amount
        currency = tx.currency.strip().upper()
        if currency == base:
            rate = Decimal("1")
        else:
            dated_rates = rates.get(currency, {})
            candidates = [rate_date for rate_date in dated_rates if rate_date <= tx.date]
            if not candidates:
                raise MissingRateError(f"missing rate for {currency} on {tx.date.isoformat()}")
            rate_date = max(candidates)
            if tx.date - rate_date > timedelta(days=7):
                raise MissingRateError(f"missing rate for {currency} on {tx.date.isoformat()}")
            rate = dated_rates[rate_date]
        conversions.append((tx, original_amount, to_money(original_amount * rate)))

    for tx, original_amount, converted_amount in conversions:
        tx.original_amount = original_amount
        tx.amount = converted_amount
    return transactions
