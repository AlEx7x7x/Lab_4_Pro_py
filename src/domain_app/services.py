"""Application / service layer: use cases and infrastructure adapters."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from domain_app.dto import Result, StoreReport
from domain_app.exceptions import (
    EmptyCartError,
    InsufficientStockError,
    StoreError,
    ValidationError,
)
from domain_app.models import (
    Cart,
    CartItem,
    Customer,
    InventoryItem,
    Order,
    Product,
    StoreCatalog,
)
from domain_app.protocols import Notifier, PaymentGateway, Repository
from domain_app.value_objects import Money, ProductId


# --------------------------------------------------------------------------
# Pricing: abstract base class + strategies (Open/Closed, Liskov)
# --------------------------------------------------------------------------
class DiscountPolicy(ABC):
    """Contract for any discount strategy."""

    @abstractmethod
    def apply(self, total: Money) -> Money:
        """Return the total after the discount."""

    def __call__(self, total: Money) -> Money:
        return self.apply(total)


class NoDiscount(DiscountPolicy):
    def apply(self, total: Money) -> Money:
        return total


class PercentageDiscount(DiscountPolicy):
    def __init__(self, percent: float) -> None:
        if not 0 <= percent <= 100:
            raise ValidationError("Invalid percent")
        self.percent = percent

    def apply(self, total: Money) -> Money:
        return total * (1 - self.percent / 100)


class FixedDiscount(DiscountPolicy):
    """New behaviour added WITHOUT modifying CheckoutService (OCP)."""

    def __init__(self, amount: Money) -> None:
        self._amount = amount

    def apply(self, total: Money) -> Money:
        if self._amount.currency != total.currency:
            raise ValidationError("Currency mismatch")
        if total <= self._amount:
            return Money.zero(total.currency)
        return Money(total.amount - self._amount.amount, total.currency)


# --------------------------------------------------------------------------
# Infrastructure adapters (they satisfy the Protocols structurally)
# --------------------------------------------------------------------------
class DemoPaymentGateway:
    def __init__(self) -> None:
        self._counter = 0

    def pay(self, amount: Money) -> str:
        self._counter += 1
        print(f"Payment processed: {amount}")
        return f"PAY-{self._counter:03d}"


class ConsoleNotifier:
    def send(self, recipient: str, message: str) -> None:
        print(f"Notification to {recipient}: {message}")


# --------------------------------------------------------------------------
# Application services
# --------------------------------------------------------------------------
class InventoryService:
    """Stock accounting use cases (single responsibility)."""

    def __init__(self, repository: Repository[InventoryItem]) -> None:
        self._repository = repository

    def register(self, product: Product, quantity: int = 0) -> InventoryItem:
        item = InventoryItem(product, quantity)
        self._repository.add(item)
        return item

    def restock(self, product_id: ProductId, amount: int) -> None:
        item = self._require(product_id)
        item.receive(amount)
        self._repository.update(item)

    def available(self, product_id: ProductId) -> int:
        item = self._repository.get(product_id)
        return 0 if item is None else item.quantity

    def ensure_available(self, items: Iterable[CartItem]) -> None:
        for cart_item in items:
            if cart_item.quantity > self.available(cart_item.product.id):
                raise InsufficientStockError(
                    f"Not enough '{cart_item.product.name}' in stock"
                )

    def write_off(self, items: Iterable[CartItem]) -> None:
        for cart_item in items:
            item = self._require(cart_item.product.id)
            item.write_off(cart_item.quantity)
            self._repository.update(item)

    def total_stock_value(self) -> Money:
        total = Money.zero()
        for item in self._repository.all():
            total = total + item.stock_value
        return total

    def low_stock(self, threshold: int) -> list[InventoryItem]:
        return [i for i in self._repository.all() if i.quantity <= threshold]

    def _require(self, product_id: ProductId) -> InventoryItem:
        item = self._repository.get(product_id)
        if item is None:
            raise InsufficientStockError(f"Product {product_id} is not stocked")
        return item


class CheckoutService:
    """Orchestrates the checkout use case; all dependencies are injected."""

    def __init__(
        self,
        payment_gateway: PaymentGateway,
        notifier: Notifier,
        discount_policy: DiscountPolicy,
        order_repository: Repository[Order],
        inventory: InventoryService,
    ) -> None:
        self._payment_gateway = payment_gateway
        self._notifier = notifier
        self._discount_policy = discount_policy
        self._orders = order_repository
        self._inventory = inventory

    def checkout(self, order_id: int, customer: Customer, cart: Cart) -> Order:
        if len(cart) == 0:
            raise EmptyCartError("Cart is empty")
        self._inventory.ensure_available(cart)

        discounted_total = self._discount_policy.apply(cart.total)
        payment_id = self._payment_gateway.pay(discounted_total)

        order = Order(
            id=order_id,
            customer=customer,
            items=tuple(CartItem(i.product, i.quantity) for i in cart),
            total=discounted_total,
        )
        order.mark_paid(payment_id)
        self._inventory.write_off(cart)
        self._orders.add(order)
        cart.clear()
        self._notifier.send(
            customer.email, f"Order paid. Payment: {payment_id}"
        )
        return order

    def try_checkout(
        self, order_id: int, customer: Customer, cart: Cart
    ) -> Result[Order]:
        """Same use case, but domain errors are returned instead of raised."""
        try:
            return Result(value=self.checkout(order_id, customer, cart))
        except StoreError as error:
            return Result(value=None, error=str(error))


class ReportService:
    """Read-only reporting over the catalog and the inventory."""

    def __init__(self, catalog: StoreCatalog, inventory: InventoryService) -> None:
        self._catalog = catalog
        self._inventory = inventory

    def build_report(self, low_stock_threshold: int = 3) -> StoreReport:
        by_category: dict[str, int] = {}
        for product in self._catalog:
            name = product.category.name
            by_category[name] = by_category.get(name, 0) + 1
        top = self._catalog.most_expensive()
        return {
            "products": len(self._catalog),
            "most_expensive": None if top is None else str(top),
            "stock_value": str(self._inventory.total_stock_value()),
            "products_by_category": by_category,
            "low_stock": [
                i.product.name
                for i in self._inventory.low_stock(low_stock_threshold)
            ],
        }
