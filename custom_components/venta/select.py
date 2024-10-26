"""Support for Venta select."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_LED_STRIP_MODE, DOMAIN
from .venta import VentaDataUpdateCoordinator
from .venta_entity import VentaSelect, VentaSelectEntityDescription

LED_STRIP_MODES = {
    0: "internal",
    2: "internal - no water",
    1: "external",
    3: "external - no water",
}
LED_STRIP_MODES_KEYS = list(LED_STRIP_MODES.keys())
LED_STRIP_MODES_VALUES = list(LED_STRIP_MODES.values())


SENSOR_TYPES: list[VentaSelectEntityDescription] = (
    VentaSelectEntityDescription(
        key=ATTR_LED_STRIP_MODE,
        translation_key=ATTR_LED_STRIP_MODE,
        entity_category=EntityCategory.CONFIG,
        exists_func=lambda coordinator: coordinator.data.action.get("LEDStripMode")
        is not None,
        value_func=lambda data: LED_STRIP_MODES.get(data.action.get("LEDStripMode")),
        action_func=(
            lambda option: {
                "Action": {
                    "LEDStripMode": LED_STRIP_MODES_KEYS[
                        LED_STRIP_MODES_VALUES.index(option)
                    ]
                }
            }
        ),
        options=LED_STRIP_MODES_VALUES,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Venta select on config_entry."""
    coordinator: VentaDataUpdateCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    entities = [
        VentaSelect(coordinator, description)
        for description in SENSOR_TYPES
        if description.exists_func(coordinator)
    ]
    async_add_entities(entities)
