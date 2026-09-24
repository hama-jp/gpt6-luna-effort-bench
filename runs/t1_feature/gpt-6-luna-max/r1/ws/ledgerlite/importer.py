"""Import bank statements from CSV.

Two formats are supported:

* ``banka`` — header ``Date,Description,Amount``. Dates are ``DD/MM/YYYY``.
  Amount is signed (``-12.50`` is an expense). An optional ``Currency`` column
  may follow ``Amount``.
* ``bankb`` — header ``Posted,Payee,Debit,Credit``. Dates are ISO ``YYYY-MM-DD``.
  Exactly one of Debit/Credit is filled; values may contain thousands
  separators, e.g. ``1,234.50``. Debit is money out. An optional ``Currency``
  column may follow ``Credit``.
"""
from __future__ import annotations

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import Transaction, to_money


class ImportErrorLL(ValueError):
    """Raised for malformed statement rows."""


def parse_banka_date(text: str) -> date:
    return datetime.strptime(text.strip(), "%d/%m/%Y").date()


def parse_bankb_date(text: str) -> date:
    return datetime.strptime(text.strip(), "%Y-%m-%d").date()


def parse_number(text: str) -> Decimal:
    cleaned = text.strip().replace(",", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ImportErrorLL(f"bad number: {text!r}") from exc


def detect_format(header: list[str]) -> str:
    cols = [c.strip().lower() for c in header]
    if cols[:3] == ["date", "description", "amount"]:
        return "banka"
    if cols[:4] == ["posted", "payee", "debit", "credit"]:
        return "bankb"
    raise ImportErrorLL(f"unknown statement format: {header}")


def _row_currency(row: list[str], index: int | None, base: str) -> str:
    if index is None or index >= len(row) or not row[index].strip():
        return base
    return row[index].strip().upper()


def _row_banka(row: list[str], source: str, base: str, currency_col: int | None) -> Transaction:
    return Transaction(
        date=parse_banka_date(row[0]),
        description=row[1].strip(),
        amount=to_money(parse_number(row[2])),
        source=source,
        currency=_row_currency(row, currency_col, base),
    )


def _row_bankb(row: list[str], source: str, base: str, currency_col: int | None) -> Transaction:
    debit, credit = row[2].strip(), row[3].strip()
    if bool(debit) == bool(credit):
        raise ImportErrorLL(f"exactly one of Debit/Credit must be set: {row}")
    amount = -parse_number(debit) if debit else parse_number(credit)
    return Transaction(
        date=parse_bankb_date(row[0]),
        description=row[1].strip(),
        amount=to_money(amount),
        source=source,
        currency=_row_currency(row, currency_col, base),
    )


def read_statement(path: str | Path, base: str = "EUR") -> list[Transaction]:
    path = Path(path)
    base = base.upper()
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            return []
        fmt = detect_format(header)
        cols = [c.strip().lower() for c in header]
        if fmt == "banka":
            parse = _row_banka
            currency_col = 3 if len(cols) > 3 and cols[3] == "currency" else None
        else:
            parse = _row_bankb
            currency_col = 4 if len(cols) > 4 and cols[4] == "currency" else None
        out = []
        for lineno, row in enumerate(reader, start=2):
            if not row or all(not c.strip() for c in row):
                continue
            try:
                out.append(parse(row, path.name, base, currency_col))
            except (IndexError, ValueError) as exc:
                raise ImportErrorLL(f"{path.name}:{lineno}: {exc}") from exc
        return out
