"""Support for Venta humidifiers."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .venta import VentaApiVersion, VentaDataUpdateCoordinator
from .venta_entity import (
    HUMIDIFIER_ENTITY_DESCRIPTION,
    VentaBaseHumidifierEntity,
    VentaV0HumidifierEntity,
    VentaV2HumidifierEntity,
    VentaV3HumidifierEntity,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Venta humidifier from config entry."""
    coordinator: VentaDataUpdateCoordinator = hass.data[DOMAIN].get(entry.entry_id)

    if coordinator.data.action.get("TargetHum") is None:
        return

    entity: VentaBaseHumidifierEntity
    if coordinator.api.device.api_version == VentaApiVersion.V0:
        entity = VentaV0HumidifierEntity(coordinator, HUMIDIFIER_ENTITY_DESCRIPTION)
    elif coordinator.api.device.api_version == VentaApiVersion.V2:
        entity = VentaV2HumidifierEntity(coordinator, HUMIDIFIER_ENTITY_DESCRIPTION)
    else:
        entity = VentaV3HumidifierEntity(coordinator, HUMIDIFIER_ENTITY_DESCRIPTION)

    async_add_entities([entity])
