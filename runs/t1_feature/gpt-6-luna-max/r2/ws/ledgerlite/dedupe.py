"""Duplicate detection across statement files.

The same purchase can appear in two exported files (e.g. overlapping date
ranges). Two transactions are duplicates when they have the same date,
currency, amount and the same *normalised* description **and come from
different source files**. Identical rows inside one file are real, separate
purchases (two coffees on the same day) and are always kept.

Normalisation: lower-case, strip, collapse runs of whitespace to one space.

When duplicates are found, the first occurrence (in input order) is kept.
If a file has N identical rows and another file has M, max(N, M) are kept.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

from .models import Transaction

_WS = re.compile(r"\s+")


def normalise(description: str) -> str:
    return _WS.sub(" ", description.strip().lower())


def _key(tx: Transaction):
    return (tx.date, tx.amount, normalise(tx.description), tx.currency.upper())


def dedupe(transactions: list[Transaction]) -> list[Transaction]:
    # how many copies of each key each source file holds
    per_source: dict[tuple, Counter] = defaultdict(Counter)
    for tx in transactions:
        per_source[_key(tx)][tx.source] += 1
    allowed = {k: max(c.values()) for k, c in per_source.items()}

    kept: list[Transaction] = []
    seen: Counter = Counter()
    for tx in transactions:
        k = _key(tx)
        if seen[k] < allowed[k]:
            kept.append(tx)
            seen[k] += 1
    return kept
