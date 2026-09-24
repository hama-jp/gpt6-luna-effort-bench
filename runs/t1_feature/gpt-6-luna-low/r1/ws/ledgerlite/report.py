"""Monthly reports.

``monthly_summary(transactions, year, month)`` covers every transaction whose
date falls in that calendar month (first to last day, inclusive).

* ``income``   — sum of positive amounts in categories that are not expense
  categories (see below)
* ``expenses`` — sum of spending per category, reported as a positive number.
  Refunds (positive amounts in an expense category) reduce that category's
  spending. A category is an expense category when its net total for the
  month is negative. ``Transfer`` is excluded from both income and expenses.
* ``net``      — income minus total expenses.
* ``top_merchants`` — the 3 descriptions with the largest total spending
  (normalised like dedupe), largest first, ties broken alphabetically.

All money values are ``Decimal`` rounded to cents.
"""
from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date
from decimal import Decimal

from .dedupe import normalise
from .models import Transaction, to_money

TRANSFER = "Transfer"


def in_month(tx: Transaction, year: int, month: int) -> bool:
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    return first <= tx.date <= last


def monthly_summary(transactions: list[Transaction], year: int, month: int, base: str = "EUR") -> dict:
    txs = [t for t in transactions if in_month(t, year, month) and t.category != TRANSFER]

    by_cat: dict[str, Decimal] = defaultdict(Decimal)
    for t in txs:
        by_cat[t.category] += t.amount

    expenses = {c: to_money(-v) for c, v in by_cat.items() if v < 0}
    expense_cats = set(expenses)
    income = to_money(sum((t.amount for t in txs if t.amount > 0 and t.category not in expense_cats), Decimal(0)))
    total_exp = to_money(sum(expenses.values(), Decimal(0)))

    merchant: dict[str, Decimal] = defaultdict(Decimal)
    for t in txs:
        if t.category in expense_cats:
            merchant[normalise(t.description)] += -t.amount
    top = sorted(((m, to_money(v)) for m, v in merchant.items() if v > 0), key=lambda mv: (-mv[1], mv[0]))[:3]

    return {
        "year": year,
        "month": month,
        "currency": base.upper(),
        "income": income,
        "expenses": dict(sorted(expenses.items())),
        "total_expenses": total_exp,
        "net": to_money(income - total_exp),
        "top_merchants": top,
    }


def format_summary(summary: dict) -> str:
    lines = [f"Report {summary['year']:04d}-{summary['month']:02d}", f"Currency: {summary['currency']}"]
    lines.append(f"Income:   {summary['income']:>10}")
    for cat, v in summary["expenses"].items():
        lines.append(f"  {cat:<20}{v:>10}")
    lines.append(f"Expenses: {summary['total_expenses']:>10}")
    lines.append(f"Net:      {summary['net']:>10}")
    if summary["top_merchants"]:
        lines.append("Top merchants:")
        for m, v in summary["top_merchants"]:
            lines.append(f"  {m:<20}{v:>10}")
    return "\n".join(lines)
