"""Light platform for Venta."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components import light
from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import color_rgb_to_hex, rgb_hex_to_rgb_list

from .const import DOMAIN
from .venta import VentaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class VentaLightEntityDescription(LightEntityDescription):
    """Describe Venta light entity."""


LIGHT_ENTITY_DESCRIPTION = VentaLightEntityDescription(
    key="light", translation_key="led_strip"
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Venta light platform."""
    coordinator: VentaDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    if coordinator.data.action.get("LEDStrip") is None:
        return
    async_add_entities([VentaLight(coordinator, LIGHT_ENTITY_DESCRIPTION)])


class VentaLight(CoordinatorEntity[VentaDataUpdateCoordinator], LightEntity):
    """Venta light."""

    _attr_has_entity_name = True
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

    def __init__(
        self,
        coordinator: VentaDataUpdateCoordinator,
        description: VentaLightEntityDescription,
    ) -> None:
        """Initialize the Venta light."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device = coordinator.api.device
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{self._device.mac}-{description.key}"
        self._attr_brightness = 255

    @property
    def is_on(self) -> bool:
        """Return if light is on."""
        return self.coordinator.data.action.get("LEDStripActive")

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the rgb color value [int, int, int]."""
        hex_string = self.coordinator.data.action.get("LEDStrip")
        return rgb_hex_to_rgb_list(hex_string[1:])

    async def async_turn_on(
        self,
        **kwargs: dict[str, Any],
    ) -> None:
        """Turn light on."""
        _LOGGER.debug("Turm on called with: %s", str(kwargs))
        if (rgb_color := kwargs.get(light.ATTR_RGB_COLOR)) is not None:
            response_data = await self._device.action(
                {
                    "Action": {
                        "LEDStrip": f"#{color_rgb_to_hex(rgb_color[0], rgb_color[1], rgb_color[2])}"
                    }
                }
            )
        else:
            response_data = await self._device.action(
                {"Action": {"LEDStripActive": True}}
            )

        if response_data is not None:
            self.coordinator.async_set_updated_data(response_data)

    async def async_turn_off(self, **kwargs: dict[str, Any]) -> None:
        """Turn light off."""
        response_data = await self._device.action({"Action": {"LEDStripActive": False}})
        if response_data is not None:
            self.coordinator.async_set_updated_data(response_data)
