"""The utility functions for the Venta components."""

from __future__ import annotations
from enum import Enum

from .venta import VentaDataUpdateCoordinator, VentaDeviceType


class VentaTimeResolution(Enum):
    """Known Venta resolution times."""

    COMMON = 5
    SERVICE_TIME = 10


def skip_zeros(
    value: str | int | bool | None,
    coordinator: VentaDataUpdateCoordinator,
    devices: list[VentaDeviceType],
) -> str | int | bool | None:
    """Skip zero values for certain devices."""
    if coordinator.api.device.device_type not in devices:
        return value
    return None if value == 0 else value


def venta_time_to_minutes(
    value: int | None, resolution: VentaTimeResolution = VentaTimeResolution.COMMON
) -> int | None:
    """Convert Venta time to minutes."""
    if value is None:
        return None

    return value * resolution.value


def venta_time_to_days_left(
    value: int | None, max_days: int, resolution=VentaTimeResolution.COMMON
) -> int | None:
    """Convert Venta time to days left."""
    if value is None:
        return None

    to_days = (60 / resolution.value) * 24
    return round(max_days - (value / to_days))


def needs_maintenance(value: int | None, max_days: int) -> bool | None:
    """Determine if the venta time means that maintenance is needed."""
    if value is None:
        return None
    return venta_time_to_days_left(value, max_days) <= 0
