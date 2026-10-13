"""Intentional type errors for the mandatory type-checking experiment."""

from domain_app.models import Category, Customer, Product
from domain_app.repositories import InMemoryRepository
from domain_app.value_objects import Money

# Error 1: str assigned to a variable annotated as int
customer_id: int = "1"


# Error 2: function annotated to return int returns str
def total() -> int:
    return "100"


# Error 3: a Customer is added to a repository of Product
repository: InMemoryRepository[Product] = InMemoryRepository()
repository.add(Customer(1, "Anna", "anna@example.com"))

# Bonus error from the lab text: wrong type of Product.id
bad_product = Product(
    id="one",
    name="Laptop",
    price=Money(100),
    category=Category(1, "Electronics"),
)
