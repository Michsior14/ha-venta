"""Support for Venta sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
    ATTR_TEMPERATURE,
    REVOLUTIONS_PER_MINUTE,
    UnitOfTime,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .venta import VentaData, VentaDataUpdateCoordinator


ATTR_WATER_LEVEL = "water_level"
ATTR_FAN_SPEED = "fan_speed"
ATTR_OPERATION_TIME = "operation_time"
ATTR_DISC_ION_TIME = "disc_ion_time"
ATTR_CLEANING_TIME = "cleaning_time"
ATTR_SERVICE_TIME = "service_time"
ATTR_SERVICE_MAX_TIME = "service_max_time"
ATTR_WARNINGS = "warnings"


@dataclass
class VentaSensorRequiredKeysMixin:
    """Mixin for required keys."""

    exists_func: Callable[[VentaDataUpdateCoordinator], bool]
    value_func: Callable[[VentaData], int | None]


@dataclass
class VentaSensorEntityDescription(
    SensorEntityDescription, VentaSensorRequiredKeysMixin
):
    """Describes Venta sensor entity."""

    suggested_display_precision = 0


SENSOR_TYPES: tuple[VentaSensorEntityDescription, ...] = (
    VentaSensorEntityDescription(
        key=ATTR_TEMPERATURE,
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        exists_func=lambda coordinator: coordinator.data.measure.get("Temperature")
        is not None,
        value_func=lambda data: data.measure.get("Temperature"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_WATER_LEVEL,
        translation_key="water_level",
        icon="mdi:water",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.measure.get("WaterLevel")
        is not None,
        value_func=lambda data: data.measure.get("WaterLevel"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_FAN_SPEED,
        translation_key="fan_speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        icon="mdi:fast-forward",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.measure.get("FanRpm")
        is not None,
        value_func=lambda data: data.measure.get("FanRpm"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_OPERATION_TIME,
        translation_key="operation_time",
        icon="mdi:power-settings",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("OperationT")
        is not None,
        value_func=lambda data: data.info.get("OperationT"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_DISC_ION_TIME,
        translation_key="disc_ion_time",
        icon="mdi:power-settings",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("DiscIonT")
        is not None,
        value_func=lambda data: data.info.get("DiscIonT"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_CLEANING_TIME,
        translation_key="cleaning_time",
        icon="mdi:power-settings",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("CleaningT")
        is not None,
        value_func=lambda data: data.info.get("CleaningT"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_SERVICE_TIME,
        translation_key="service_time",
        icon="mdi:power-settings",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("ServiceT")
        is not None,
        value_func=lambda data: data.info.get("ServiceT"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_SERVICE_MAX_TIME,
        translation_key="service_max_time",
        icon="mdi:power-settings",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("ServiceMax")
        is not None,
        value_func=lambda data: data.info.get("ServiceMax"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_WARNINGS,
        translation_key="warnings",
        icon="mdi:alert",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("Warnings")
        is not None,
        value_func=lambda data: data.info.get("Warnings"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Venta sensors on config_entry."""
    coordinator: VentaDataUpdateCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    sensors = [
        ATTR_TEMPERATURE,
        ATTR_WATER_LEVEL,
        ATTR_FAN_SPEED,
        ATTR_OPERATION_TIME,
        ATTR_DISC_ION_TIME,
        ATTR_CLEANING_TIME,
        ATTR_SERVICE_TIME,
        ATTR_SERVICE_MAX_TIME,
        ATTR_WARNINGS,
    ]
    entities = [
        VentaSensor(coordinator, description)
        for description in SENSOR_TYPES
        if description.key in sensors and description.exists_func(coordinator)
    ]
    async_add_entities(entities)


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
        return self.entity_description.value_func(self.coordinator.data)
