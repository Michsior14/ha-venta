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
from .venta import VentaDataUpdateCoordinator, VentaDeviceType, VentaApiVersion

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

    entity: VentaBaseHumidifierEntity
    if coordinator.api.device.api_version == VentaApiVersion.V0:
        entity = VentaV0HumidifierEntity(coordinator, HUMIDIFIER_ENTITY_DESCRIPTION)
    if coordinator.api.device.api_version == VentaApiVersion.V2:
        entity = VentaV2HumidifierEntity(coordinator, HUMIDIFIER_ENTITY_DESCRIPTION)
    else:
        entity = VentaV3HumidifierEntity(coordinator, HUMIDIFIER_ENTITY_DESCRIPTION)

    async_add_entities([entity])


class VentaBaseHumidifierEntity(
    CoordinatorEntity[VentaDataUpdateCoordinator], HumidifierEntity
):
    """Venta base humidifier device."""

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
        if MODE_SLEEP in self._attr_available_modes and data.action.get("SleepMode"):
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

    async def async_turn_on(self, **kwargs: dict[str, Any]) -> None:
        """Turn the device on."""
        await self._send_action({"Power": True})

    async def async_turn_off(self, **kwargs: dict[str, Any]) -> None:
        """Turn the device off."""
        await self._send_action({"Power": False})

    async def async_set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        await self._send_action({"TargetHum": humidity})

    async def async_set_mode(self, mode: str) -> None:
        """Set new target preset mode."""
        action = {"Power": True}
        if mode == MODE_AUTO:
            action.update({"SleepMode": False, "Automatic": True})
        elif mode == MODE_SLEEP:
            action.update({"SleepMode": True})
        else:
            level = int(mode[-1])
            action.update({"SleepMode": False, "Automatic": False, "FanSpeed": level})

        await self._send_action(action)

    def _map_to_action(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map data to protocol based json action."""
        return {
            "Action": data,
        }

    async def _send_action(self, data: dict[str, Any]) -> None:
        """Send action to device."""
        await self._device.action(self._map_to_action(data))
        await self.coordinator.async_request_refresh()


class VentaV0HumidifierEntity(VentaBaseHumidifierEntity):
    """Venta humidifier device for protocol version 0."""


class VentaV2HumidifierEntity(VentaBaseHumidifierEntity):
    """Venta humidifier device for protocol version 2."""


class VentaV3HumidifierEntity(VentaBaseHumidifierEntity):
    """Venta humidifier device for protocol version 3."""

    def __init__(
        self,
        coordinator: VentaDataUpdateCoordinator,
        description: VentaHumidifierEntityDescription,
    ) -> None:
        """Initialize Venta V3 humidifier."""
        super().__init__(coordinator, description)
        if coordinator.api.device.device_type == VentaDeviceType.AH550_AH555:
            self._attr_available_modes = [
                MODE_AUTO,
                MODE_LEVEL_1,
                MODE_LEVEL_2,
                MODE_LEVEL_3,
            ]

    def _map_to_action(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            **data,
            "Action": "control",
        }

    async def async_turn_on(self, **kwargs: dict[str, Any]) -> None:
        """Turn the device on."""
        state = self.coordinator.data.action
        action = {
            "Power": True,
            "Automatic": state.get("Automatic"),
            "FanSpeed": state.get("FanSpeed"),
        }
        if not action.get("Automatic"):
            action.update({"SleepMode": state.get("SleepMode")})
        await self._send_action(action)

    async def async_turn_off(self, **kwargs: dict[str, Any]) -> None:
        """Turn the device off."""
        state = self.coordinator.data.action
        action = {
            "Power": False,
            "Automatic": state.get("Automatic"),
            "FanSpeed": state.get("FanSpeed"),
        }
        if not action.get("Automatic"):
            action.update({"SleepMode": state.get("SleepMode")})
        await self._send_action(action)

    async def async_set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        state = self.coordinator.data.action
        await self._send_action(
            {
                "Power": state.get("Power"),
                "Automatic": state.get("Automatic"),
                "TargetHum": humidity,
            }
        )

    async def async_set_mode(self, mode: str) -> None:
        """Set new target preset mode."""
        state = self.coordinator.data.action

        action = {
            "Power": True,
        }
        if mode == MODE_AUTO:
            action.update({"Automatic": True})
        elif mode == MODE_SLEEP:
            action = {"SleepMode": True}
        else:
            level = int(mode[-1])
            action.update(
                {
                    "SleepMode": state.get("SleepMode"),
                    "Automatic": False,
                    "FanSpeed": level,
                }
            )

        await self._send_action(action)
