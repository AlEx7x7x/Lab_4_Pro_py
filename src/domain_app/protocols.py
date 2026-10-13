"""Structural interfaces (Protocols) used for dependency inversion.

Interfaces are intentionally small (Interface Segregation Principle).
"""

from typing import Protocol, TypeVar, runtime_checkable

from domain_app.value_objects import Money


class HasId(Protocol):
    """Anything with a read-only integer ``id``."""

    @property
    def id(self) -> int: ...


T = TypeVar("T", bound=HasId)


class Repository(Protocol[T]):
    """Storage abstraction for entities that have an ``id``."""

    def add(self, item: T) -> None: ...

    def update(self, item: T) -> None: ...

    def get(self, item_id: int) -> T | None: ...

    def all(self) -> list[T]: ...

    def remove(self, item_id: int) -> bool: ...


class PaymentGateway(Protocol):
    """Payment abstraction: returns the payment identifier."""

    def pay(self, amount: Money) -> str: ...


class Notifier(Protocol):
    """Notification abstraction."""

    def send(self, recipient: str, message: str) -> None: ...


@runtime_checkable
class Serializable(Protocol):
    """Objects that can be converted to a plain dictionary."""

    def to_dict(self) -> dict[str, object]: ...
