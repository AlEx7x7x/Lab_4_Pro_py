"""Immutable value objects."""

from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering
from typing import TypeAlias

from domain_app.exceptions import ValidationError

ProductId: TypeAlias = int

DEFAULT_CURRENCY = "UAH"


@total_ordering
@dataclass(frozen=True, slots=True)
class Money:
    """Amount of money in a given currency (immutable value object)."""

    amount: float
    currency: str = DEFAULT_CURRENCY

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValidationError("Money amount cannot be negative")
        if not self.currency:
            raise ValidationError("Currency must not be empty")

    @classmethod
    def zero(cls, currency: str = DEFAULT_CURRENCY) -> Money:
        return cls(0.0, currency)

    def _ensure_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValidationError("Currency mismatch")

    def __add__(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor: float) -> Money:
        return Money(round(self.amount * factor, 2), self.currency)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._ensure_same_currency(other)
        return self.amount < other.amount

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"
