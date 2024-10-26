"""Set of utilities to work with json strings."""

from __future__ import annotations

from collections.abc import Callable
from json import JSONDecodeError, JSONDecoder, loads
from re import Pattern
from typing import Any, Generator


class _RawJSONDecoder(JSONDecoder):
    """JSON decoder that stops at the first valid JSON object."""

    index: int
    end_hook: Callable[[int], None] | None

    def __init__(  # noqa: PLR0913
        self,
        *,
        object_hook: Callable[[dict[str, Any]], Any] | None = None,
        parse_float: Callable[[str], Any] | None = None,
        parse_int: Callable[[str], Any] | None = None,
        parse_constant: Callable[[str], Any] | None = None,
        strict: bool = True,
        object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] | None = None,
        index: int = 0,
        end_hook: Callable[[int], None] | None = None,
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
        self.end_hook = end_hook

    def decode(self, s: str, *_: type[Pattern.match]) -> dict[str, Any]:
        """Decode the JSON string."""
        data, end = self.raw_decode(s, self.index)
        if self.end_hook:
            self.end_hook(end)
        return data


def extract_json(value: str, index: int = 0) -> Generator[dict[str, Any]]:
    """Extract JSON from any string."""
    context = {"end": len(value)}
    while (index := value.find("{", index)) != -1:
        try:
            yield loads(
                value,
                cls=_RawJSONDecoder,
                index=index,
                end_hook=lambda end: context.update(end=end),
            )
            index = context["end"]
        except JSONDecodeError:
            index += 1
