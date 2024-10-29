"""Venta AH500 setup functions."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import (
    ATTR_BOX_OPEN,
    ATTR_FAN_BLOCKED,
    ATTR_HUMIDITY,
    ATTR_NEEDS_REFILL,
    ATTR_NEEDS_SERVICE,
    ATTR_OPERATION_TIME,
    ATTR_SERVICE_MAX_TIME,
    ATTR_SERVICE_TIME,
    ATTR_SLEEP_MODE,
    ATTR_TIME_TO_SERVICE,
    ATTR_WARNINGS,
    MODES_3,
    SERVICE_TIME_DAYS,
    TEN_MINUTES_RESOLUTION,
)
from ..utils import venta_time_to_days_left, venta_time_to_minutes
from ..venta import VentaDataUpdateCoordinator
from ..venta_entity import (
    VentaBinarySensor,
    VentaBinarySensorEntityDescription,
    VentaSensor,
    VentaSensorEntityDescription,
    VentaSwitch,
    VentaSwitchEntityDescription,
    VentaV3HumidifierEntity,
)

WATER_WARNING = 1
SERVICE_WARNING = 2
BOX_OPEN_WARNING = 4
FAN_BLOCKED_WARNING = 8


async def async_setup_humidifier(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up humidifiers for Venta AH500."""
    async_add_entities([VentaV3HumidifierEntity(coordinator, modes=[*MODES_3])])


async def async_setup_binary_sensor(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors for Venta AH500."""
    descriptions = [
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_REFILL,
            translation_key=ATTR_NEEDS_REFILL,
            icon="mdi:water-alert",
            value_func=lambda data: data.info.get("Warnings") & WATER_WARNING,
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_SERVICE,
            translation_key=ATTR_NEEDS_SERVICE,
            icon="mdi:account-wrench",
            value_func=lambda data: data.info.get("Warnings") & SERVICE_WARNING,
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_BOX_OPEN,
            translation_key=ATTR_BOX_OPEN,
            icon="mdi:open-in-app",
            value_func=lambda data: data.info.get("Warnings") & BOX_OPEN_WARNING,
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_FAN_BLOCKED,
            translation_key=ATTR_FAN_BLOCKED,
            icon="mdi:fan-alert",
            value_func=lambda data: data.info.get("Warnings") & FAN_BLOCKED_WARNING,
        ),
    ]
    async_add_entities(
        [VentaBinarySensor(coordinator, description) for description in descriptions]
    )


async def async_setup_sensor(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors for Venta AH500."""
    descriptions = [
        VentaSensorEntityDescription(
            key=ATTR_OPERATION_TIME,
            translation_key=ATTR_OPERATION_TIME,
            icon="mdi:timer",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("OperationT"), TEN_MINUTES_RESOLUTION
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_TIME_TO_SERVICE,
            translation_key=ATTR_TIME_TO_SERVICE,
            icon="mdi:wrench-clock",
            native_unit_of_measurement=UnitOfTime.DAYS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_days_left(
                coordinator.data.info.get("ServiceT"),
                SERVICE_TIME_DAYS,
                TEN_MINUTES_RESOLUTION,
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_SERVICE_TIME,
            translation_key=ATTR_SERVICE_TIME,
            icon="mdi:timer",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("ServiceT"), TEN_MINUTES_RESOLUTION
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_SERVICE_MAX_TIME,
            translation_key=ATTR_SERVICE_MAX_TIME,
            icon="mdi:timer",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("ServiceMax"), TEN_MINUTES_RESOLUTION
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_TEMPERATURE,
            translation_key=ATTR_TEMPERATURE,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            suggested_display_precision=1,
            value_func=lambda coordinator: coordinator.data.measure.get("Temperature"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_HUMIDITY,
            translation_key=ATTR_HUMIDITY,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
            suggested_display_precision=1,
            value_func=lambda coordinator: coordinator.data.measure.get("Humidity"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_WARNINGS,
            translation_key=ATTR_WARNINGS,
            icon="mdi:alert",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: coordinator.data.info.get("Warnings"),
        ),
    ]
    async_add_entities(
        [VentaSensor(coordinator, description) for description in descriptions]
    )


async def async_setup_switch(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up switches for Venta AH500."""
    descriptions = [
        VentaSwitchEntityDescription(
            key=ATTR_SLEEP_MODE,
            translation_key=ATTR_SLEEP_MODE,
            entity_category=EntityCategory.CONFIG,
            value_func=lambda data: data.action.get("SleepMode"),
            action_func=lambda data, is_on: (
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
            ),
        ),
    ]
    async_add_entities(
        [VentaSwitch(coordinator, description) for description in descriptions]
    )


async def async_setup_light(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up lights for Venta AH500."""
    pass


async def async_setup_select(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up selects for Venta AH500."""
    pass
