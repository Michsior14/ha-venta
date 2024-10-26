"""Set of utilities to work with json strings."""

from __future__ import annotations

from collections.abc import Callable
from json import JSONDecodeError, JSONDecoder, loads
from re import Pattern
from typing import Any, Generator


class RawJSONDecoder(JSONDecoder):
    """JSON decoder that stops at the first valid JSON object."""

    end: int | None = None
    index: int

    def __init__(  # noqa: PLR0913
        self,
        index: int,
        *,
        object_hook: Callable[[dict[str, Any]], Any] | None = None,
        parse_float: Callable[[str], Any] | None = None,
        parse_int: Callable[[str], Any] | None = None,
        parse_constant: Callable[[str], Any] | None = None,
        strict: bool = True,
        object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] | None = None,
    ) -> None:
        """Initialize the decoder."""
        super().__init__(
            object_hook=object_hook,
            parse_float=parse_float,
            parse_int=parse_int,
            parse_constant=parse_constant,
            strict=strict,
            object_pairs_hook=object_pairs_hook,
        )
        self.index = index

    def decode(self, s: str, *_: type[Pattern.match]) -> dict[str, Any]:
        """Decode the JSON string."""
        data, self.__class__.end = self.raw_decode(s, self.index)
        return data


def extract_json(value: str, index: int = 0) -> Generator[dict[str, Any]]:
    """Extract JSON from any string."""
    while (index := value.find("{", index)) != -1:
        try:
            decoder = RawJSONDecoder(index)
            yield loads(value, cls=decoder)
            index = decoder.end
        except JSONDecodeError:
            index += 1
