"""Demonstration scenario for the online-shop object model."""

from domain_app.dto import (
    ProductPayload,
    product_from_payload,
    product_to_payload,
    summarize_order,
)
from domain_app.models import (
    Cart,
    Category,
    Customer,
    DigitalProduct,
    InventoryItem,
    Order,
    PhysicalProduct,
    Product,
    StoreCatalog,
)
from domain_app.protocols import Serializable
from domain_app.repositories import InMemoryRepository
from domain_app.services import (
    CheckoutService,
    ConsoleNotifier,
    DemoPaymentGateway,
    FixedDiscount,
    InventoryService,
    PercentageDiscount,
    ReportService,
)
from domain_app.value_objects import Money


def build_checkout(
    inventory: InventoryService,
    orders: InMemoryRepository[Order],
) -> CheckoutService:
    """Composition root: the only place that knows concrete classes."""
    return CheckoutService(
        payment_gateway=DemoPaymentGateway(),
        notifier=ConsoleNotifier(),
        discount_policy=PercentageDiscount(10),
        order_repository=orders,
        inventory=inventory,
    )


def main() -> None:
    electronics = Category(1, "Electronics")
    accessories = Category(2, "Accessories")
    books = Category(3, "Books")

    laptop = PhysicalProduct(
        id=1, name="Laptop", price=Money(35_000), category=electronics, weight_kg=2.1
    )
    monitor = PhysicalProduct(
        id=2, name="Monitor", price=Money(9_500), category=electronics, weight_kg=4.8
    )
    mouse = PhysicalProduct(
        id=3, name="Mouse", price=Money(1_200), category=accessories, weight_kg=0.1
    )
    ebook = DigitalProduct(
        id=4, name="Python e-book", price=Money(300), category=books, file_size_mb=12
    )

    # --- catalog (repository injected into StoreCatalog) -------------------
    catalog = StoreCatalog(InMemoryRepository[Product]())
    for product in (laptop, monitor, mouse, ebook):
        catalog.add_product(product)

    print("== Catalog ==")
    print("Products:", len(catalog))
    print("Search 'mo':", [p.name for p in catalog.search("mo")])
    print("Electronics:", [p.name for p in catalog.by_category(electronics)])
    top = catalog.most_expensive()
    print("Most expensive:", top)
    print("Laptop < Monitor:", laptop.price < monitor.price)

    # --- inventory ----------------------------------------------------------
    inventory = InventoryService(InMemoryRepository[InventoryItem]())
    inventory.register(laptop, 5)
    inventory.register(monitor, 3)
    inventory.register(mouse, 20)
    inventory.register(ebook, 999)
    print("\n== Inventory ==")
    print("Stock value:", inventory.total_stock_value())
    print("Mouse in stock:", inventory.available(mouse.id))

    # --- cart ---------------------------------------------------------------
    cart = Cart()
    cart.add(laptop, quantity=1)
    cart.add(mouse, quantity=2)
    print("\n== Cart ==")
    print("Cart items:", len(cart))
    print("Laptop in cart:", 1 in cart)
    print("First item:", cart[0].product.name)
    print("Original total:", cart.total)

    # --- checkout (dependency injection) -----------------------------------
    orders = InMemoryRepository[Order]()
    service = build_checkout(inventory, orders)
    customer = Customer(id=1, name="Anna Koval", email="anna@example.com")

    print("\n== Checkout ==")
    order = service.checkout(order_id=1001, customer=customer, cart=cart)
    print("\nCreated order:")
    print("ID:", order.id)
    print("Status:", order.status.value)
    print("Final total:", order.total)
    print("Items:", len(order))
    print("Summary:", summarize_order(order))
    print("Mouse in stock after order:", inventory.available(mouse.id))

    # --- errors are returned as Result[Order] ------------------------------
    print("\n== Error handling ==")
    empty_result = service.try_checkout(1002, customer, Cart())
    print("Empty cart ->", empty_result.success, "|", empty_result.error)

    big_cart = Cart()
    big_cart.add(monitor, quantity=10)
    stock_result = service.try_checkout(1003, customer, big_cart)
    print("Too many monitors ->", stock_result.success, "|", stock_result.error)

    # --- strategy: another discount without changing CheckoutService --------
    fixed = FixedDiscount(Money(500))
    print("\nFixed discount on 1200.00 UAH:", fixed(Money(1_200)))

    # --- TypedDict -> domain object -----------------------------------------
    payload: ProductPayload = {
        "id": 5,
        "name": "Keyboard",
        "price": 2_500.0,
        "currency": "UAH",
        "category_id": 2,
        "category_name": "Accessories",
        "kind": "physical",
        "weight_kg": 0.9,
    }
    keyboard = product_from_payload(payload)
    catalog.add_product(keyboard)
    inventory.register(keyboard, 2)
    print("\n== TypedDict ==")
    print("From payload:", keyboard)
    print("Back to payload:", product_to_payload(keyboard))
    print("Product is Serializable:", isinstance(keyboard, Serializable))
    print("Cart is Serializable:", isinstance(cart, Serializable))

    # --- report ---------------------------------------------------------------
    print("\n== Report ==")
    report = ReportService(catalog, inventory).build_report()
    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
