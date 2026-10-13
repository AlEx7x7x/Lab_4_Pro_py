"""Variant A (hard-wired dependency) vs variant B (dependency injection)."""

from domain_app.protocols import PaymentGateway
from domain_app.services import DemoPaymentGateway
from domain_app.value_objects import Money


class OrderServiceA:
    """Variant A: the service creates its concrete dependency itself."""

    def __init__(self) -> None:
        self.gateway = DemoPaymentGateway()

    def pay(self, amount: Money) -> str:
        return self.gateway.pay(amount)


class OrderServiceB:
    """Variant B: the dependency is injected through an abstraction."""

    def __init__(self, gateway: PaymentGateway) -> None:
        self.gateway = gateway

    def pay(self, amount: Money) -> str:
        return self.gateway.pay(amount)


class RecordingGateway:
    """Test double: records calls instead of printing / calling a real API."""

    def __init__(self) -> None:
        self.calls: list[Money] = []

    def pay(self, amount: Money) -> str:
        self.calls.append(amount)
        return "TEST-PAY"


class AuditedGateway:
    """Another implementation: wraps any gateway (extension without edits)."""

    def __init__(self, inner: PaymentGateway) -> None:
        self._inner = inner
        self.log: list[str] = []

    def pay(self, amount: Money) -> str:
        payment_id = self._inner.pay(amount)
        self.log.append(f"{payment_id}:{amount}")
        return payment_id


def main() -> None:
    print("Variant A - hard-wired DemoPaymentGateway:")
    OrderServiceA().pay(Money(100))  # real side effect, cannot be replaced

    print("\nVariant B - test double injected:")
    fake = RecordingGateway()
    result = OrderServiceB(fake).pay(Money(100))
    print("payment id:", result, "| recorded calls:", [str(c) for c in fake.calls])

    print("\nVariant B - gateway replaced by a decorator, service unchanged:")
    audited = AuditedGateway(DemoPaymentGateway())
    OrderServiceB(audited).pay(Money(250))
    print("audit log:", audited.log)


if __name__ == "__main__":
    main()
