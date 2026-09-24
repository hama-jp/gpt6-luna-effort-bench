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
    # Each source may contain multiple genuine identical purchases. Across
    # sources, keep only the largest per-source multiplicity for each key.
    counts: dict[tuple, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for tx in transactions:
        counts[_key(tx)][tx.source] += 1

    limits = {key: max(source_counts.values()) for key, source_counts in counts.items()}
    kept: list[Transaction] = []
    emitted: dict[tuple, int] = defaultdict(int)
    for tx in transactions:
        key = _key(tx)
        if emitted[key] < limits[key]:
            kept.append(tx)
            emitted[key] += 1
    return kept
