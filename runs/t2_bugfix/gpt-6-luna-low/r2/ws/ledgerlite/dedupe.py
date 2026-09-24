"""Duplicate detection across statement files.

The same purchase can appear in two exported files (e.g. overlapping date
ranges). Two transactions are duplicates when they have the same date, the
same amount and the same *normalised* description **and come from different
source files**. Identical rows inside one file are real, separate purchases
(two coffees on the same day) and are always kept.

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
    return (tx.date, tx.amount, normalise(tx.description))


def dedupe(transactions: list[Transaction]) -> list[Transaction]:
    # Count each key by source. A repeated row within one source is a
    # separate purchase; overlapping files contribute only the largest count.
    grouped: dict[tuple, dict[str, list[Transaction]]] = defaultdict(lambda: defaultdict(list))
    for tx in transactions:
        grouped[_key(tx)][tx.source].append(tx)
    limits = {key: max(map(len, sources.values())) for key, sources in grouped.items()}
    used: Counter = Counter()
    kept = []
    for tx in transactions:
        key = _key(tx)
        if used[key] < limits[key]:
            kept.append(tx)
            used[key] += 1
    return kept
