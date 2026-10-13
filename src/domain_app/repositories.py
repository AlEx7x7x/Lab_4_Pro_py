"""Concrete repository implementations."""

from collections.abc import Callable
from typing import Generic

from domain_app.exceptions import DuplicateEntityError, EntityNotFoundError
from domain_app.protocols import T


class InMemoryRepository(Generic[T]):
    """Generic in-memory repository; satisfies ``Repository[T]`` structurally."""

    def __init__(self) -> None:
        self._items: dict[int, T] = {}

    def add(self, item: T) -> None:
        if item.id in self._items:
            raise DuplicateEntityError(f"Entity with id={item.id} already exists")
        self._items[item.id] = item

    def update(self, item: T) -> None:
        if item.id not in self._items:
            raise EntityNotFoundError(f"Entity with id={item.id} not found")
        self._items[item.id] = item

    def get(self, item_id: int) -> T | None:
        return self._items.get(item_id)

    def all(self) -> list[T]:
        return list(self._items.values())

    def remove(self, item_id: int) -> bool:
        return self._items.pop(item_id, None) is not None

    def find(self, predicate: Callable[[T], bool]) -> list[T]:
        return [item for item in self._items.values() if predicate(item)]

    def __len__(self) -> int:
        return len(self._items)
