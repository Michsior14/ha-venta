"""Support for Venta switch."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_SLEEP_MODE, DOMAIN
from .venta import VentaDataUpdateCoordinator, VentaDeviceType
from .venta_entity import VentaSwitch, VentaSwitchEntityDescription

SENSOR_TYPES: list[VentaSwitchEntityDescription] = (
    VentaSwitchEntityDescription(
        key=ATTR_SLEEP_MODE,
        translation_key=ATTR_SLEEP_MODE,
        entity_category=EntityCategory.CONFIG,
        exists_func=lambda coordinator: coordinator.api.device.device_type
        == VentaDeviceType.AH550_AH555,
        value_func=lambda data: data.action.get("SleepMode"),
        action_func=(
            lambda data, is_on: (
                {
                    "SleepMode": True,
                    "Action": "control",
                }
                if is_on
                else {
                    "Power": data.action.get("Power"),
                    "SleepMode": False,
                    "Automatic": data.action.get("Automatic"),
                    "FanSpeed": data.action.get("FanSpeed"),
                    "Action": "control",
                }
            )
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Venta switch on config_entry."""
    coordinator: VentaDataUpdateCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    entities = [
        VentaSwitch(coordinator, description)
        for description in SENSOR_TYPES
        if description.exists_func(coordinator)
    ]
    async_add_entities(entities)
