"""Support for Venta switch."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_SLEEP_MODE, DOMAIN
from .venta import VentaData, VentaDataUpdateCoordinator, VentaDeviceType


@dataclass
class VentaSwitchRequiredKeysMixin:
    """Mixin for required keys."""

    exists_func: Callable[[VentaDataUpdateCoordinator], bool]
    value_func: Callable[[VentaData], str | None]
    action_func: Callable[[VentaData, bool], dict | None]


@dataclass
class VentaSwitchEntityDescription(
    SwitchEntityDescription, VentaSwitchRequiredKeysMixin
):
    """Describes Venta switch entity."""


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


class VentaSwitch(CoordinatorEntity[VentaDataUpdateCoordinator], SwitchEntity):
    """Representation of a switch."""

    _attr_has_entity_name = True
    entity_description: VentaSwitchEntityDescription

    def __init__(
        self,
        coordinator: VentaDataUpdateCoordinator,
        description: VentaSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{coordinator.api.device.mac}-{description.key}"
        self._device = coordinator.api.device

    @property
    def is_on(self) -> str | None:
        """Return if switch is on."""
        return self.entity_description.value_func(self.coordinator.data)

    async def async_turn_on(self, **kwargs: dict[str, Any]) -> None:
        """Turn the switch on."""
        await self._send_action(True)

    async def async_turn_off(self, **kwargs: dict[str, Any]) -> None:
        """Turn the switch off."""
        await self._send_action(False)

    async def _send_action(self, on: bool) -> None:
        """Send action to the device."""
        await self._device.action(
            self.entity_description.action_func(self.coordinator.data, on),
            self.coordinator,
        )
