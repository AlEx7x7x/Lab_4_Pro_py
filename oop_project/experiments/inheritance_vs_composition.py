"""Same behaviour implemented with inheritance and with composition."""

from abc import ABC, abstractmethod
from typing import Protocol


# ------------------------------ inheritance --------------------------------
class BaseProcessor(ABC):
    @abstractmethod
    def parse(self, raw: str) -> list[str]: ...

    def validate(self, values: list[str]) -> list[str]:
        return [v for v in values if v]

    def format(self, values: list[str]) -> str:
        return ", ".join(values)

    def process(self, raw: str) -> str:
        return self.format(self.validate(self.parse(raw)))


class CsvProcessor(BaseProcessor):
    def parse(self, raw: str) -> list[str]:
        return [part.strip() for part in raw.split(",")]


class UpperCsvProcessor(CsvProcessor):
    """Needs a new subclass for every new combination of behaviours."""

    def format(self, values: list[str]) -> str:
        return ", ".join(v.upper() for v in values)


# ------------------------------ composition --------------------------------
class Parser(Protocol):
    def parse(self, raw: str) -> list[str]: ...


class Validator(Protocol):
    def validate(self, values: list[str]) -> list[str]: ...


class Formatter(Protocol):
    def format(self, values: list[str]) -> str: ...


class CsvParser:
    def parse(self, raw: str) -> list[str]:
        return [part.strip() for part in raw.split(",")]


class SemicolonParser:
    def parse(self, raw: str) -> list[str]:
        return [part.strip() for part in raw.split(";")]


class NonEmptyValidator:
    def validate(self, values: list[str]) -> list[str]:
        return [v for v in values if v]


class PlainFormatter:
    def format(self, values: list[str]) -> str:
        return ", ".join(values)


class UpperFormatter:
    def format(self, values: list[str]) -> str:
        return ", ".join(v.upper() for v in values)


class Processor:
    """Has-a Parser, Validator and Formatter: any combination, no subclasses."""

    def __init__(
        self, parser: Parser, validator: Validator, formatter: Formatter
    ) -> None:
        self._parser = parser
        self._validator = validator
        self._formatter = formatter

    def process(self, raw: str) -> str:
        return self._formatter.format(
            self._validator.validate(self._parser.parse(raw))
        )


def main() -> None:
    data = "a, b,, c"
    print("Inheritance  CsvProcessor      :", CsvProcessor().process(data))
    print("Inheritance  UpperCsvProcessor :", UpperCsvProcessor().process(data))

    validator = NonEmptyValidator()
    print(
        "Composition  csv + plain       :",
        Processor(CsvParser(), validator, PlainFormatter()).process(data),
    )
    print(
        "Composition  csv + upper       :",
        Processor(CsvParser(), validator, UpperFormatter()).process(data),
    )
    print(
        "Composition  semicolon + upper :",
        Processor(SemicolonParser(), validator, UpperFormatter()).process("x;y;;z"),
    )


if __name__ == "__main__":
    main()
