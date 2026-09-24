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
    return _WS.sub(" ", description.strip()).casefold()


def _key(tx: Transaction):
    return (tx.date, tx.amount, normalise(tx.description))


def dedupe(transactions: list[Transaction]) -> list[Transaction]:
    kept: list[Transaction] = []
    # Track occurrence counts per source. A row can be discarded only when
    # another source already contributes that same occurrence.
    seen: dict[tuple, Counter] = defaultdict(Counter)
    kept_count: Counter = Counter()
    for tx in transactions:
        k = _key(tx)
        counts = seen[k]
        prior_max = max(counts.values(), default=0)
        counts[tx.source] += 1
        # Preserve each new occurrence from a source, up to the largest
        # multiplicity represented by any source seen so far.
        if kept_count[k] < max(prior_max, counts[tx.source]):
            kept.append(tx)
            kept_count[k] += 1
    return kept
