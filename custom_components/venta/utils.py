"""The utility functions for the Venta components."""

from __future__ import annotations

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, List, TypeVar

from homeassistant.const import UnitOfTemperature

_LOGGER = logging.getLogger(__name__)


def skip_zeros(
    value: str | int | bool | None,
) -> str | int | bool | None:
    """Skip zero values for certain devices."""
    return None if value == 0 else value


def venta_time_to_minutes(value: int | None, resolution: int) -> int | None:
    """Convert Venta time to minutes."""
    if value is None:
        return None

    return value * resolution


def venta_time_to_days_left(
    value: int | None,
    max_days: int,
    resolution: int,
) -> int | None:
    """Convert Venta time to days left."""
    if value is None:
        return None

    to_days = (60 / resolution) * 24
    return round(max_days - (value / to_days))


def needs_maintenance(value: int | None, max_days: int, resolution: int) -> bool | None:
    """Determine if the venta time means that maintenance is needed."""
    if value is None:
        return None
    return venta_time_to_days_left(value, max_days, resolution) <= 0


_T = TypeVar("_T")


def get_from_list(list: List[_T] | None, index: int, default: _T = None) -> _T:
    """Get an item from a list or return a default value."""
    if list is None:
        return default
    try:
        return list[index]
    except IndexError:
        return default


def venta_temperature_unit(value: int | None) -> str | None:
    """Return the temperature unit for Venta devices that supports TempUnit field."""
    if value is None:
        return None
    return UnitOfTemperature.CELSIUS if value == 0 else UnitOfTemperature.FAHRENHEIT


def retry_on_timeout(retries: int = 5, timeout: int = 10, delay: int = 0.5) -> Callable:
    """Retry a function on timeout and with a delay."""

    def decorator(fun: Callable) -> Callable:
        @wraps(fun)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            for attempt in range(retries):
                try:
                    async with asyncio.timeout(timeout):
                        return await fun(*args, **kwargs)
                except asyncio.TimeoutError:
                    _LOGGER.warning(
                        "Timeout calling %s, retrying... (attempt %d/%d)",
                        fun.__name__,
                        attempt,
                        retries,
                    )
                    await asyncio.sleep(delay)
            _LOGGER.error("Retries exhausted calling %s, giving up...", fun.__name__)
            return None

        return wrapper

    return decorator
