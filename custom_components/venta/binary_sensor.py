"""Support for Venta binary sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_NEEDS_REFILL, ATTR_NEEDS_SERVICE, DOMAIN, NO_WATER_THRESHOLD
from .venta import VentaData, VentaDataUpdateCoordinator, VentaDeviceType


@dataclass
class VentaSensorRequiredKeysMixin:
    """Mixin for required keys."""

    value_func: Callable[[VentaData], bool | None]


@dataclass
class VentaBinarySensorEntityDescription(
    BinarySensorEntityDescription, VentaSensorRequiredKeysMixin
):
    """Describes Venta binary sensor entity."""


def _supported_sensors(
    device_type: VentaDeviceType,
) -> list[VentaBinarySensorEntityDescription]:
    """Return supported sensors for given device type."""
    match device_type:
        case VentaDeviceType.LW73_LW74 | VentaDeviceType.UNKNOWN:
            service_warnings = [16, 17]
            return [
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_REFILL,
                    translation_key="needs_refill",
                    icon="mdi:water-alert",
                    value_func=(
                        lambda data: data.info.get("Warnings") != 0
                        and data.measure.get("WaterLevel") < NO_WATER_THRESHOLD
                    ),
                ),
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_SERVICE,
                    translation_key="needs_service",
                    icon="mdi:account-wrench",
                    value_func=(
                        lambda data: data.info.get("Warnings") in service_warnings
                    ),
                ),
            ]
        case VentaDeviceType.AH550_AH555:
            return [
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_REFILL,
                    translation_key="needs_refill",
                    icon="mdi:water-alert",
                    value_func=(lambda data: data.info.get("Warnings") == 1),
                ),
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_SERVICE,
                    translation_key="needs_service",
                    icon="mdi:account-wrench",
                    value_func=(
                        lambda data: data.info.get("ServiceT") is not None
                        and data.info.get("ServiceT") >= data.info.get("ServiceMax")
                    ),
                ),
            ]
        case _:
            return []


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Venta binary sensors on config_entry."""
    coordinator: VentaDataUpdateCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    entities = [
        VentaBinarySensor(coordinator, description)
        for description in _supported_sensors(coordinator.api.device.device_type)
        if description.key
    ]
    async_add_entities(entities)


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
