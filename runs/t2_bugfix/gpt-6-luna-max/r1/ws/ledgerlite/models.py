"""Core data types."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def to_money(value) -> Decimal:
    """Round to cents, half-up (the rounding rule used everywhere in ledgerlite)."""
    # Converting through str avoids importing the binary approximation when
    # callers pass a float (for example, 2.675 should round to 2.68).
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass
class Transaction:
    """One line of a bank statement.

    ``amount`` is signed: negative = money out (expense), positive = money in.
    ``source`` is the name of the file the transaction was imported from.
    """

    date: date
    description: str
    amount: Decimal
    source: str = ""
    category: str = "Uncategorized"
    tags: list[str] = field(default_factory=list)

    @property
    def is_expense(self) -> bool:
        return self.amount < 0
