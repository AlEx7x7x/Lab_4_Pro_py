# Lab 4 — Typed OOP model of an online shop (variant 3)

Typed object model: entities, value objects, ABC, Protocol, generic
repository, TypedDict, dependency injection, static checking with mypy.

## Layout

```
oop_project/
├── pyproject.toml
├── README.md
├── src/domain_app/
│   ├── __init__.py
│   ├── main.py            # demo scenario
│   ├── models.py          # domain entities
│   ├── value_objects.py   # Money (frozen dataclass)
│   ├── protocols.py       # Protocol interfaces
│   ├── repositories.py    # generic in-memory repository
│   ├── services.py        # application / service layer
│   ├── dto.py             # TypedDict payloads, Result[T]
│   └── exceptions.py      # custom exception hierarchy
├── tests/test_shop.py
└── experiments/           # DI, inheritance vs composition, type errors
```

## Run

```
python -m pip install -e ".[dev]"
python -m domain_app.main        # or: shop-demo
python -m pytest
mypy src tests experiments       # expected: Success: no issues found
mypy experiments/type_errors_demo.py   # intentional errors (3)
```
