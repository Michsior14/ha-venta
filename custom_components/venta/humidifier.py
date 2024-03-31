"""Support for Venta humidifiers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.humidifier import (
    MODE_AUTO,
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityDescription,
    HumidifierEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MODE_SLEEP,
    MODES_3,
    MODES_4,
    MODES_5,
)
from .venta import VentaApiVersion, VentaDataUpdateCoordinator, VentaDeviceType

DEFAULT_MODES: list[str] = [MODE_SLEEP, *MODES_3]

DEVICE_MODES: dict[VentaDeviceType, list[str]] = {
    VentaDeviceType.LW60: [MODE_SLEEP, *MODES_5],
    # VentaDeviceType.LW62: [MODE_SLEEP, *MODES_5],
    VentaDeviceType.LW73_LW74: [MODE_SLEEP, *MODES_4],
    VentaDeviceType.AH550_AH555: MODES_3,
}


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


class VentaBaseHumidifierEntity(
    CoordinatorEntity[VentaDataUpdateCoordinator], HumidifierEntity
):
    """Venta base humidifier device."""

    _attr_has_entity_name = True
    _attr_device_class = HumidifierDeviceClass.HUMIDIFIER
    _attr_supported_features = HumidifierEntityFeature.MODES
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
        self._attr_available_modes = DEVICE_MODES.get(
            self._device.device_type, DEFAULT_MODES
        )

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
        self.coordinator.async_set_updated_data(
            await self._device.action(self._map_to_action(data))
        )


class VentaV0HumidifierEntity(VentaBaseHumidifierEntity):
    """Venta humidifier device for protocol version 0."""

    async def async_set_mode(self, mode: str) -> None:
        """Set new target preset mode."""
        action = {}
        if mode == MODE_AUTO:
            action = {"Automatic": True}
        elif mode == MODE_SLEEP:
            action = {"SleepMode": True}
        else:
            action = {"FanSpeed": int(mode[-1])}
        await self._send_action(action)


class VentaV2HumidifierEntity(VentaBaseHumidifierEntity):
    """Venta humidifier device for protocol version 2."""


class VentaV3HumidifierEntity(VentaBaseHumidifierEntity):
    """Venta humidifier device for protocol version 3."""

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
