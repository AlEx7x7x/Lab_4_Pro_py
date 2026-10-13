"""Unit tests: dependency injection makes the use case easy to test."""

import pytest

from domain_app.exceptions import (
    DuplicateEntityError,
    EmptyCartError,
    InsufficientStockError,
    ValidationError,
)
from domain_app.models import (
    Cart,
    Category,
    Customer,
    InventoryItem,
    Order,
    OrderStatus,
    PhysicalProduct,
    Product,
)
from domain_app.repositories import InMemoryRepository
from domain_app.services import (
    CheckoutService,
    FixedDiscount,
    InventoryService,
    NoDiscount,
    PercentageDiscount,
)
from domain_app.value_objects import Money


class FakeGateway:
    def __init__(self) -> None:
        self.paid: list[Money] = []

    def pay(self, amount: Money) -> str:
        self.paid.append(amount)
        return "FAKE-1"


class FakeNotifier:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def send(self, recipient: str, message: str) -> None:
        self.messages.append((recipient, message))


CATEGORY = Category(1, "Electronics")


def make_product(product_id: int = 1, price: float = 100.0) -> Product:
    return PhysicalProduct(
        id=product_id,
        name=f"Item{product_id}",
        price=Money(price),
        category=CATEGORY,
        weight_kg=1.0,
    )


def make_service(
    stock: int = 10,
) -> tuple[CheckoutService, FakeGateway, FakeNotifier, InventoryService]:
    inventory = InventoryService(InMemoryRepository[InventoryItem]())
    inventory.register(make_product(1), stock)
    gateway = FakeGateway()
    notifier = FakeNotifier()
    service = CheckoutService(
        payment_gateway=gateway,
        notifier=notifier,
        discount_policy=PercentageDiscount(10),
        order_repository=InMemoryRepository[Order](),
        inventory=inventory,
    )
    return service, gateway, notifier, inventory


CUSTOMER = Customer(1, "Test", "test@example.com")


def test_checkout_pays_discounted_total_and_writes_off_stock() -> None:
    service, gateway, notifier, inventory = make_service(stock=10)
    cart = Cart()
    cart.add(make_product(1, 100.0), 2)
    order = service.checkout(1, CUSTOMER, cart)
    assert order.status is OrderStatus.PAID
    assert gateway.paid == [Money(180.0)]
    assert inventory.available(1) == 8
    assert notifier.messages[0][0] == "test@example.com"
    assert len(cart) == 0


def test_checkout_empty_cart_raises() -> None:
    service, *_ = make_service()
    with pytest.raises(EmptyCartError):
        service.checkout(1, CUSTOMER, Cart())


def test_checkout_insufficient_stock_returns_failed_result() -> None:
    service, gateway, *_ = make_service(stock=1)
    cart = Cart()
    cart.add(make_product(1), 5)
    result = service.try_checkout(1, CUSTOMER, cart)
    assert not result.success
    assert gateway.paid == []


def test_money_is_immutable_and_validated() -> None:
    with pytest.raises(ValidationError):
        Money(-1)
    with pytest.raises(AttributeError):
        Money(1).amount = 5  # type: ignore[misc]
    assert Money(1) + Money(2) == Money(3)
    assert Money(1) < Money(2)


def test_inventory_item_encapsulation() -> None:
    item = InventoryItem(make_product(), 2)
    with pytest.raises(ValidationError):
        item.quantity = -5
    with pytest.raises(InsufficientStockError):
        item.write_off(3)


def test_discount_policies() -> None:
    total = Money(1_000)
    assert NoDiscount()(total) == total
    assert PercentageDiscount(25)(total) == Money(750)
    assert FixedDiscount(Money(300))(total) == Money(700)
    assert FixedDiscount(Money(5_000))(total) == Money.zero()


def test_repository_rejects_duplicates() -> None:
    repo = InMemoryRepository[Product]()
    repo.add(make_product(1))
    with pytest.raises(DuplicateEntityError):
        repo.add(make_product(1))
