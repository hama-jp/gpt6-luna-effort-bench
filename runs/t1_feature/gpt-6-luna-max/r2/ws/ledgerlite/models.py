"""Core data types."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def to_money(value) -> Decimal:
    """Round to cents, half-up (the rounding rule used everywhere in ledgerlite)."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass
class Transaction:
    """One line of a bank statement.

    ``amount`` is signed: negative = money out (expense), positive = money in.
    It is denominated in ``currency`` until converted; ``original_amount``
    retains that value after conversion. ``source`` is the name of the file
    the transaction was imported from.
    """

    date: date
    description: str
    amount: Decimal
    source: str = ""
    category: str = "Uncategorized"
    tags: list[str] = field(default_factory=list)
    currency: str = "EUR"
    original_amount: Decimal | None = None

    def __post_init__(self) -> None:
        self.currency = self.currency.strip().upper()

    @property
    def is_expense(self) -> bool:
        return self.amount < 0
