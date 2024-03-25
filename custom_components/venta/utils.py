"""The utility functions for the Venta components."""

from __future__ import annotations

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
