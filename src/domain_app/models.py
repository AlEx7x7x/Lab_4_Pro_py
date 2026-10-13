"""Domain entities of the online shop."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum

from domain_app.exceptions import (
    EntityNotFoundError,
    InsufficientStockError,
    InvalidOrderStateError,
    ValidationError,
)
from domain_app.protocols import Repository
from domain_app.value_objects import Money, ProductId


@dataclass(frozen=True)
class Category:
    """Product category."""

    id: int
    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("Category name must not be empty")


@dataclass
class Product:
    """Base product (parent class of the inheritance hierarchy)."""

    id: ProductId
    name: str
    price: Money
    category: Category

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValidationError("Product id must be positive")
        if not self.name.strip():
            raise ValidationError("Product name must not be empty")

    @property
    def requires_shipping(self) -> bool:
        return True

    @property
    def label(self) -> str:
        return f"{self.name} [{self.category.name}]"

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price.amount,
            "currency": self.price.currency,
            "category": self.category.name,
        }

    def __str__(self) -> str:
        return f"{self.name} ({self.price})"


@dataclass
class PhysicalProduct(Product):
    """Product that is delivered to the customer."""

    weight_kg: float

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.weight_kg <= 0:
            raise ValidationError("Weight must be positive")


@dataclass
class DigitalProduct(Product):
    """Downloadable product: no shipping is required."""

    file_size_mb: float

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.file_size_mb <= 0:
            raise ValidationError("File size must be positive")

    @property
    def requires_shipping(self) -> bool:
        return False


class InventoryItem:
    """Stock record: encapsulates the quantity of one product."""

    def __init__(self, product: Product, quantity: int = 0) -> None:
        self.product = product
        self._quantity = 0
        self.quantity = quantity  # goes through the validating setter

    @property
    def id(self) -> int:
        return self.product.id

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if value < 0:
            raise ValidationError("Quantity cannot be negative")
        self._quantity = value

    @property
    def stock_value(self) -> Money:
        return self.product.price * self._quantity

    def receive(self, amount: int) -> None:
        if amount <= 0:
            raise ValidationError("Receipt amount must be positive")
        self._quantity += amount

    def write_off(self, amount: int) -> None:
        if amount <= 0:
            raise ValidationError("Write-off amount must be positive")
        if amount > self._quantity:
            raise InsufficientStockError(
                f"Only {self._quantity} pcs of '{self.product.name}' in stock, "
                f"{amount} requested"
            )
        self._quantity -= amount

    def __repr__(self) -> str:
        return (
            f"InventoryItem(product={self.product.name!r}, "
            f"quantity={self._quantity!r})"
        )


@dataclass
class Customer:
    id: int
    name: str
    email: str

    def __post_init__(self) -> None:
        if "@" not in self.email:
            raise ValidationError("Invalid e-mail address")


@dataclass
class CartItem:
    product: Product
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")

    @property
    def total(self) -> Money:
        return self.product.price * self.quantity


@dataclass
class Cart:
    """Shopping cart: a custom collection of ``CartItem`` objects."""

    items: list[CartItem] = field(default_factory=list)

    def add(self, product: Product, quantity: int = 1) -> None:
        for item in self.items:
            if item.product.id == product.id:
                item.quantity += quantity
                return
        self.items.append(CartItem(product=product, quantity=quantity))

    def clear(self) -> None:
        self.items.clear()

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[CartItem]:
        return iter(self.items)

    def __getitem__(self, index: int) -> CartItem:
        return self.items[index]

    def __contains__(self, product_id: ProductId) -> bool:
        return any(item.product.id == product_id for item in self.items)

    @property
    def total(self) -> Money:
        total = Money.zero()
        for item in self.items:
            total = total + item.total
        return total


class OrderStatus(str, Enum):
    NEW = "new"
    PAID = "paid"
    CANCELLED = "cancelled"


@dataclass
class Order:
    id: int
    customer: Customer
    items: tuple[CartItem, ...]
    total: Money
    status: OrderStatus = OrderStatus.NEW
    payment_id: str | None = None

    def mark_paid(self, payment_id: str) -> None:
        if self.status is not OrderStatus.NEW:
            raise InvalidOrderStateError("Only a new order can be paid")
        self.payment_id = payment_id
        self.status = OrderStatus.PAID

    def cancel(self) -> None:
        if self.status is not OrderStatus.NEW:
            raise InvalidOrderStateError("Only a new order can be cancelled")
        self.status = OrderStatus.CANCELLED

    def __len__(self) -> int:
        return len(self.items)

    def __str__(self) -> str:
        return f"Order #{self.id} [{self.status.value}] {self.total}"


class StoreCatalog:
    """Catalog of products backed by an injected repository."""

    def __init__(self, repository: Repository[Product]) -> None:
        self._repository = repository

    def add_product(self, product: Product) -> None:
        self._repository.add(product)

    def get(self, product_id: ProductId) -> Product:
        product = self._repository.get(product_id)
        if product is None:
            raise EntityNotFoundError(f"Product {product_id} not found")
        return product

    def search(self, text: str) -> list[Product]:
        needle = text.casefold()
        return [p for p in self._repository.all() if needle in p.name.casefold()]

    def by_category(self, category: Category) -> list[Product]:
        return [p for p in self._repository.all() if p.category == category]

    def most_expensive(self) -> Product | None:
        products = self._repository.all()
        if not products:
            return None
        return max(products, key=lambda p: p.price)

    def __len__(self) -> int:
        return len(self._repository.all())

    def __iter__(self) -> Iterator[Product]:
        return iter(self._repository.all())
