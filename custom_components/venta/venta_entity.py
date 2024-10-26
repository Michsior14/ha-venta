"""Venta entities definitions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.humidifier import (
    MODE_AUTO,
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityDescription,
    HumidifierEntityFeature,
)
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import MODE_SLEEP, MODES_3, MODES_4, MODES_5
from .venta import VentaData, VentaDataUpdateCoordinator, VentaDeviceType


@dataclass
class VentaBinarySensorRequiredKeysMixin:
    """Mixin for required keys."""

    value_func: Callable[[VentaData], bool | None]


@dataclass
class VentaBinarySensorEntityDescription(
    BinarySensorEntityDescription, VentaBinarySensorRequiredKeysMixin
):
    """Describes Venta binary sensor entity."""


class VentaBinarySensor(
    CoordinatorEntity[VentaDataUpdateCoordinator], BinarySensorEntity
):
    """Representation of a binary sensor."""

    _attr_has_entity_name = True
    entity_description: VentaBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: VentaDataUpdateCoordinator,
        description: VentaBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{coordinator.api.device.mac}-{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        return self.entity_description.value_func(self.coordinator.data)


@dataclass
class VentaHumidifierEntityDescription(HumidifierEntityDescription):
    """Describe Venta humidifier entity."""


DEFAULT_MODES: list[str] = [MODE_SLEEP, *MODES_3]

DEVICE_MODES: dict[VentaDeviceType, list[str]] = {
    VentaDeviceType.LW60: [MODE_SLEEP, *MODES_5],
    # VentaDeviceType.LW62: [MODE_SLEEP, *MODES_5],
    VentaDeviceType.LW73_LW74: [MODE_SLEEP, *MODES_4],
    VentaDeviceType.AH550_AH555: MODES_3,
}

HUMIDIFIER_ENTITY_DESCRIPTION = VentaHumidifierEntityDescription(
    key=HumidifierDeviceClass.HUMIDIFIER,
    translation_key=HumidifierDeviceClass.HUMIDIFIER,
    device_class=HumidifierDeviceClass.HUMIDIFIER,
)


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
        return f"level_{level}"

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


@dataclass
class VentaSensorRequiredKeysMixin:
    """Mixin for required keys."""

    exists_func: Callable[[VentaDataUpdateCoordinator], bool]
    value_func: Callable[[VentaDataUpdateCoordinator], int | None]


@dataclass
class VentaSensorEntityDescription(
    SensorEntityDescription, VentaSensorRequiredKeysMixin
):
    """Describes Venta sensor entity."""

    suggested_display_precision = 0


class VentaSensor(CoordinatorEntity[VentaDataUpdateCoordinator], SensorEntity):
    """Representation of a Sensor."""

    _attr_has_entity_name = True
    entity_description: VentaSensorEntityDescription

    def __init__(
        self,
        coordinator: VentaDataUpdateCoordinator,
        description: VentaSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{coordinator.api.device.mac}-{description.key}"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        return self.entity_description.value_func(self.coordinator)


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
        self.coordinator.async_set_updated_data(
            await self._device.action(
                self.entity_description.action_func(self.coordinator.data, on)
            )
        )


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
