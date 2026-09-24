"""Load exchange rates and convert transactions to a reporting currency."""
from __future__ import annotations

import bisect
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import Transaction, to_money


class MissingRateError(ValueError):
    """Raised when no sufficiently recent rate is available for a transaction."""


def load_rates(path: str | Path) -> dict[str, dict[date, Decimal]]:
    """Read rates from a CSV with ``date,currency,rate`` columns.

    The returned mapping is keyed by uppercase currency code, then by rate date.
    A rate is the amount of the base currency represented by one unit of the
    keyed currency.
    """
    rates: dict[str, dict[date, Decimal]] = {}
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = [col.strip().lower() for col in next(reader)]
        except StopIteration:
            raise ValueError("rates CSV is empty; expected date,currency,rate header") from None

        try:
            date_col = header.index("date")
            currency_col = header.index("currency")
            rate_col = header.index("rate")
        except ValueError:
            raise ValueError("rates CSV must have date,currency,rate columns") from None

        for lineno, row in enumerate(reader, start=2):
            if not row or all(not cell.strip() for cell in row):
                continue
            try:
                date_text = row[date_col].strip()
                rate_date = date.fromisoformat(date_text)
                if rate_date.isoformat() != date_text:
                    raise ValueError(f"invalid ISO date: {date_text!r}")
                currency = row[currency_col].strip().upper()
                if not currency:
                    raise ValueError("currency code is empty")
                rate = Decimal(row[rate_col].strip())
            except (IndexError, ValueError, InvalidOperation) as exc:
                raise ValueError(f"rates CSV line {lineno}: {exc}") from exc
            rates.setdefault(currency, {})[rate_date] = rate
    return rates


def convert(
    transactions: list[Transaction],
    rates: dict[str, dict[date, Decimal]],
    base: str = "EUR",
) -> list[Transaction]:
    """Convert each transaction in place to ``base`` and return the list."""
    base = base.upper()
    sorted_rates = {
        currency.upper(): sorted(currency_rates.items())
        for currency, currency_rates in rates.items()
    }
    rate_dates = {currency: [entry[0] for entry in entries] for currency, entries in sorted_rates.items()}

    for tx in transactions:
        currency = tx.currency.upper()
        tx.currency = currency
        tx.original_amount = tx.amount
        if currency == base:
            tx.amount = to_money(tx.original_amount)
            continue

        entries = sorted_rates.get(currency, [])
        dates = rate_dates.get(currency, [])
        position = bisect.bisect_right(dates, tx.date) - 1
        if position < 0 or tx.date - entries[position][0] > timedelta(days=7):
            raise MissingRateError(f"missing exchange rate for {currency} on {tx.date.isoformat()}")
        tx.amount = to_money(tx.original_amount * entries[position][1])
    return transactions
