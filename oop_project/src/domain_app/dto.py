"""DTOs: TypedDict payloads for external data and a generic Result."""

from dataclasses import dataclass
from typing import Generic, Literal, NotRequired, TypedDict, TypeVar

from domain_app.models import (
    Category,
    DigitalProduct,
    Order,
    PhysicalProduct,
    Product,
)
from domain_app.value_objects import Money

V = TypeVar("V")


class ProductPayload(TypedDict):
    """JSON-like representation of a product (external data)."""

    id: int
    name: str
    price: float
    currency: str
    category_id: int
    category_name: str
    kind: NotRequired[Literal["simple", "physical", "digital"]]
    weight_kg: NotRequired[float]
    file_size_mb: NotRequired[float]


class OrderSummary(TypedDict):
    order_id: int
    customer_email: str
    items: int
    total: str
    status: str


class StoreReport(TypedDict):
    products: int
    most_expensive: str | None
    stock_value: str
    products_by_category: dict[str, int]
    low_stock: list[str]


@dataclass
class Result(Generic[V]):
    """Outcome of an operation: either a value or an error message."""

    value: V | None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None


def product_from_payload(data: ProductPayload) -> Product:
    """Convert an external payload into a validated domain object."""
    category = Category(data["category_id"], data["category_name"])
    price = Money(data["price"], data["currency"])
    kind = data.get("kind", "simple")
    if kind == "physical":
        return PhysicalProduct(
            id=data["id"],
            name=data["name"],
            price=price,
            category=category,
            weight_kg=data.get("weight_kg", 1.0),
        )
    if kind == "digital":
        return DigitalProduct(
            id=data["id"],
            name=data["name"],
            price=price,
            category=category,
            file_size_mb=data.get("file_size_mb", 1.0),
        )
    return Product(id=data["id"], name=data["name"], price=price, category=category)


def product_to_payload(product: Product) -> ProductPayload:
    payload: ProductPayload = {
        "id": product.id,
        "name": product.name,
        "price": product.price.amount,
        "currency": product.price.currency,
        "category_id": product.category.id,
        "category_name": product.category.name,
        "kind": "simple",
    }
    if isinstance(product, PhysicalProduct):
        payload["kind"] = "physical"
        payload["weight_kg"] = product.weight_kg
    elif isinstance(product, DigitalProduct):
        payload["kind"] = "digital"
        payload["file_size_mb"] = product.file_size_mb
    return payload


def summarize_order(order: Order) -> OrderSummary:
    return {
        "order_id": order.id,
        "customer_email": order.customer.email,
        "items": len(order),
        "total": str(order.total),
        "status": order.status.value,
    }
