"""Support for Venta select."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_LED_STRIP_MODE, DOMAIN
from .venta import VentaData, VentaDataUpdateCoordinator

LED_STRIP_MODES = {
    0: "internal",
    2: "internal - no water",
    1: "external",
    3: "external - no water",
}
LED_STRIP_MODES_KEYS = list(LED_STRIP_MODES.keys())
LED_STRIP_MODES_VALUES = list(LED_STRIP_MODES.values())


@dataclass
class VentaSelectRequiredKeysMixin:
    """Mixin for required keys."""

    exists_func: Callable[[VentaDataUpdateCoordinator], bool]
    value_func: Callable[[VentaData], str | None]
    action_func: Callable[[str], dict | None]


@dataclass
class VentaSelectEntityDescription(
    SelectEntityDescription, VentaSelectRequiredKeysMixin
):
    """Describes Venta select entity."""


SENSOR_TYPES: list[VentaSelectEntityDescription] = (
    VentaSelectEntityDescription(
        key=ATTR_LED_STRIP_MODE,
        translation_key="led_strip_mode",
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


class VentaSelect(CoordinatorEntity[VentaDataUpdateCoordinator], SelectEntity):
    """Representation of a select."""

    _attr_has_entity_name = True
    entity_description: VentaSelectEntityDescription

    def __init__(
        self,
        coordinator: VentaDataUpdateCoordinator,
        description: VentaSelectEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{coordinator.api.device.mac}-{description.key}"
        self._attr_options = description.options

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return self.entity_description.value_func(self.coordinator.data)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.api.device.status(
            self.entity_description.action_func(option)
        )
        await self.coordinator.async_request_refresh()
