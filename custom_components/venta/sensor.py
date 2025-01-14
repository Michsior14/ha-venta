"""Support for Venta sensors."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
)
from .venta import VentaDataUpdateCoordinator
from .venta_device import async_setup_device


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Venta sensors on config_entry."""
    coordinator: VentaDataUpdateCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    await async_setup_device("sensor", hass, coordinator, async_add_entities)
