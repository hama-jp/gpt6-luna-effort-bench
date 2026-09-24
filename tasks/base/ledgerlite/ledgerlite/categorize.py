"""Rule-based categorisation.

Rules file format (one rule per line, ``#`` starts a comment)::

    <priority> | <pattern> | <category>

* ``pattern`` is a case-insensitive substring of the description, or a regular
  expression when prefixed with ``re:`` (matched with ``re.search``,
  case-insensitive).
* When several rules match, the one with the **highest** priority wins.
  Ties are broken by the order in the file (earlier line wins).
* Transactions that match no rule keep the category ``Uncategorized``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .models import Transaction


@dataclass
class Rule:
    priority: int
    pattern: str
    category: str
    line: int

    def matches(self, description: str) -> bool:
        if self.pattern.startswith("re:"):
            return re.search(self.pattern[3:], description, re.IGNORECASE) is not None
        return self.pattern.lower() in description.lower()


def parse_rules(text: str) -> list[Rule]:
    rules = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            raise ValueError(f"rules line {lineno}: expected 3 fields")
        rules.append(Rule(int(parts[0]), parts[1], parts[2], lineno))
    return rules


def load_rules(path: str | Path) -> list[Rule]:
    return parse_rules(Path(path).read_text(encoding="utf-8"))


def categorize(transactions: list[Transaction], rules: list[Rule]) -> list[Transaction]:
    ordered = sorted(rules, key=lambda r: (-r.priority, r.line))
    for tx in transactions:
        for rule in ordered:
            if rule.matches(tx.description):
                tx.category = rule.category
                break
        else:
            tx.category = "Uncategorized"
    return transactions
