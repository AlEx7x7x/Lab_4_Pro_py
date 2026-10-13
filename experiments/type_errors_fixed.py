"""The same code after fixing all type errors."""

from domain_app.models import Category, Customer, Product
from domain_app.repositories import InMemoryRepository
from domain_app.value_objects import Money

customer_id: int = 1


def total() -> int:
    return 100


product_repository: InMemoryRepository[Product] = InMemoryRepository()
product_repository.add(
    Product(
        id=1,
        name="Laptop",
        price=Money(100),
        category=Category(1, "Electronics"),
    )
)

customer_repository: InMemoryRepository[Customer] = InMemoryRepository()
customer_repository.add(Customer(1, "Anna", "anna@example.com"))

good_product = Product(
    id=1,
    name="Laptop",
    price=Money(100),
    category=Category(1, "Electronics"),
)

if __name__ == "__main__":
    print(customer_id, total(), len(product_repository), good_product)
