"""Foreign exchange rate loading and transaction conversion."""
from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import Transaction, to_money


class MissingRateError(ValueError):
    """No sufficiently recent exchange rate exists for a transaction."""


def load_rates(path: str | Path) -> dict[str, dict[date, Decimal]]:
    """Load ``date,currency,rate`` CSV rates into currency/date mappings."""
    rates: dict[str, dict[date, Decimal]] = {}
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            header = []
        columns = [c.strip().lower() for c in header]
        if columns != ["date", "currency", "rate"]:
            raise ValueError("rates CSV must have header date,currency,rate")
        for values in reader:
            try:
                day_text, currency_text, rate_text = values
                day = date.fromisoformat(day_text.strip())
                currency = currency_text.strip().upper()
                rate = Decimal(rate_text.strip())
            except (ValueError, AttributeError, InvalidOperation) as exc:
                raise ValueError(f"invalid rate row: {values}") from exc
            if not currency:
                raise ValueError(f"invalid rate row: {values}")
            rates.setdefault(currency, {})[day] = rate
    return rates


def convert(transactions: list[Transaction], rates: dict[str, dict[date, Decimal]], base: str = "EUR") -> list[Transaction]:
    """Convert transactions in place to ``base`` using same-day or recent rates."""
    base = base.upper()
    for tx in transactions:
        currency = tx.currency.upper()
        tx.currency = currency
        tx.original_amount = tx.amount
        if currency == base:
            tx.amount = to_money(tx.original_amount)
            continue

        currency_rates = rates.get(currency, {})
        eligible_days = [day for day in currency_rates if day <= tx.date]
        rate_day = max(eligible_days) if eligible_days else None
        if rate_day is None or (tx.date - rate_day).days > 7:
            raise MissingRateError(f"missing rate for {currency} on {tx.date.isoformat()}")
        tx.amount = to_money(tx.original_amount * currency_rates[rate_day])
    return transactions
