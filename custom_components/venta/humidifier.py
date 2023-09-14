"""Support for Venta humidifiers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


from homeassistant.components.humidifier import (
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityDescription,
    HumidifierEntityFeature,
    MODE_AUTO,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MODE_SLEEP,
    MODE_LEVEL_1,
    MODE_LEVEL_2,
    MODE_LEVEL_3,
    MODE_LEVEL_4,
)
from .venta import VentaDataUpdateCoordinator

AVAILABLE_MODES = [
    MODE_AUTO,
    MODE_SLEEP,
    MODE_LEVEL_1,
    MODE_LEVEL_2,
    MODE_LEVEL_3,
    MODE_LEVEL_4,
]


@dataclass
class VentaHumidifierEntityDescription(HumidifierEntityDescription):
    """Describe Venta humidifier entity."""


HUMIDIFIER_ENTITY_DESCRIPTION = VentaHumidifierEntityDescription(
    key=HumidifierDeviceClass.HUMIDIFIER,
    translation_key="humidifier",
    device_class=HumidifierDeviceClass.HUMIDIFIER,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Venta humidifier from config entry."""
    coordinator: VentaDataUpdateCoordinator = hass.data[DOMAIN].get(entry.entry_id)

    async_add_entities(
        [VentaHumidifierEntity(coordinator, HUMIDIFIER_ENTITY_DESCRIPTION)]
    )


class VentaHumidifierEntity(
    CoordinatorEntity[VentaDataUpdateCoordinator], HumidifierEntity
):
    """Venta humidifier Device."""

    _attr_has_entity_name = True
    _attr_device_class = HumidifierDeviceClass.HUMIDIFIER
    _attr_supported_features = HumidifierEntityFeature.MODES
    _attr_available_modes = AVAILABLE_MODES
    entity_description: VentaHumidifierEntityDescription

    def __init__(
        self,
        coordinator: VentaDataUpdateCoordinator,
        description: VentaHumidifierEntityDescription,
    ) -> None:
        """Initialize Venta humidifier."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device = coordinator.api.device
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{self._device.mac}-{description.key}"

    @property
    def is_on(self) -> bool:
        """Return the device is on or off."""
        return self.coordinator.data.action.get("Power", False)

    @property
    def mode(self) -> str | None:
        """Return the current mode."""
        data = self.coordinator.data
        if data.action.get("Automatic"):
            return MODE_AUTO
        if data.action.get("SleepMode"):
            return MODE_SLEEP
        level = data.action.get("FanSpeed", 1)
        return f"level {level}"

    @property
    def target_humidity(self) -> int | None:
        """Return the humidity we try to reach."""
        return self.coordinator.data.action.get("TargetHum")

    @property
    def current_humidity(self) -> int | None:
        """Return the current humidity."""
        return self.coordinator.data.measure.get("Humidity")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        await self._device.update({"Action": {"Power": True}})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self._device.update({"Action": {"Power": False}})
        await self.coordinator.async_request_refresh()

    async def async_set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        await self._device.update({"Action": {"TargetHum": humidity}})
        await self.coordinator.async_request_refresh()

    async def async_set_mode(self, mode: str) -> None:
        """Set new target preset mode."""
        if mode == MODE_AUTO:
            await self._device.update(
                {"Action": {"Power": True, "SleepMode": False, "Automatic": True}}
            )
        elif mode == MODE_SLEEP:
            await self._device.update({"Action": {"Power": True, "SleepMode": True}})
        else:
            level = int(mode[-1])
            await self._device.update(
                {
                    "Action": {
                        "Power": True,
                        "SleepMode": False,
                        "Automatic": False,
                        "FanSpeed": level,
                    }
                }
            )
        await self.coordinator.async_request_refresh()
