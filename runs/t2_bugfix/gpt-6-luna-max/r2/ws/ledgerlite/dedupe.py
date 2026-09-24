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
from collections import defaultdict

from .models import Transaction

_WS = re.compile(r"\s+")


def normalise(description: str) -> str:
    return _WS.sub(" ", description.strip().lower())


def _key(tx: Transaction):
    return (tx.date, tx.amount, normalise(tx.description))


def dedupe(transactions: list[Transaction]) -> list[Transaction]:
    kept: list[Transaction] = []
    counts_by_source: dict[tuple, dict[str, int]] = defaultdict(dict)
    max_count: dict[tuple, int] = defaultdict(int)
    for tx in transactions:
        k = _key(tx)
        source_counts = counts_by_source[k]
        occurrence = source_counts.get(tx.source, 0) + 1
        source_counts[tx.source] = occurrence
        if occurrence > max_count[k]:
            kept.append(tx)
            max_count[k] = occurrence
    return kept
