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
    # For each key, the occurrence number within its source identifies a
    # purchase. Keep the first source's row for each occurrence number. This
    # preserves repeated purchases within a file while removing overlap across
    # files, and yields max(per-source count) rows for each key.
    kept: list[Transaction] = []
    seen_occurrences: dict[tuple, set[int]] = defaultdict(set)
    source_counts: dict[tuple, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for tx in transactions:
        k = _key(tx)
        source = tx.source
        source_counts[k][source] += 1
        occurrence = source_counts[k][source]
        if occurrence not in seen_occurrences[k]:
            kept.append(tx)
            seen_occurrences[k].add(occurrence)
    return kept
