"""Custom exception hierarchy of the shop domain."""


class StoreError(Exception):
    """Base class for all domain errors."""


class ValidationError(StoreError, ValueError):
    """An object was created or changed with invalid data."""


class DuplicateEntityError(StoreError):
    """An entity with the same id already exists in a repository."""


class EntityNotFoundError(StoreError):
    """An entity with the requested id does not exist."""


class InsufficientStockError(StoreError):
    """Not enough items in stock for the requested operation."""


class EmptyCartError(StoreError):
    """Checkout was requested for an empty cart."""


class InvalidOrderStateError(StoreError):
    """The requested transition is not allowed for the order status."""
