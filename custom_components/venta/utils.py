"""The utility functions for the Venta components."""

from __future__ import annotations

from collections.abc import Callable
from json import JSONDecodeError, JSONDecoder, loads
from re import Pattern
from typing import Any, Generator

from .venta import VentaDataUpdateCoordinator, VentaDeviceType


def skip_zeros(
    value: str | int | bool | None,
    coordinator: VentaDataUpdateCoordinator,
    devices: list[VentaDeviceType],
) -> str | int | bool | None:
    """Skip zero values for certain devices."""
    if coordinator.api.device.device_type not in devices:
        return value
    return None if value == 0 else value


def venta_time_to_minutes(value: int | None) -> int | None:
    """Convert Venta time to minutes."""
    if value is None:
        return None

    # It appears that Venta uses 10 minute intervals for time
    to_minutes = 10
    return value * to_minutes


def venta_time_to_days_left(value: int | None, max_days: int) -> int | None:
    """Convert Venta time to days left."""
    if value is None:
        return None

    to_days = 6 * 24
    return round(max_days - (value / to_days))


def needs_maintenance(value: int | None, max_days: int) -> bool | None:
    """Determine if the venta time means that maintenance is needed."""
    if value is None:
        return None
    return venta_time_to_days_left(value, max_days) <= 0


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
