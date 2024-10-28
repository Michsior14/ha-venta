"""Venta LW73 setup functions."""

from __future__ import annotations

from homeassistant.components.humidifier.const import MODE_SLEEP
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import (
    ATTR_CLEANING_TIME,
    ATTR_DISC_ION_TIME,
    ATTR_DISC_ION_TIME_TO_REPLACE,
    ATTR_FAN_SPEED,
    ATTR_HUMIDITY,
    ATTR_LED_STRIP_MODE,
    ATTR_NEEDS_CLEANING,
    ATTR_NEEDS_DISC_REPLACEMENT,
    ATTR_NEEDS_REFILL,
    ATTR_NEEDS_SERVICE,
    ATTR_OPERATION_TIME,
    ATTR_SERVICE_TIME,
    ATTR_TIME_TO_CLEAN,
    ATTR_TIME_TO_SERVICE,
    ATTR_WARNINGS,
    ATTR_WATER_LEVEL,
    CLEAN_TIME_DAYS,
    FIVE_MINUTES_RESOLUTION,
    ION_DISC_REPLACE_TIME_DAYS,
    LED_STRIP_MODES_EXTERNAL,
    LED_STRIP_MODES_EXTERNAL_NO_WATER,
    LED_STRIP_MODES_INTERNAL,
    LED_STRIP_MODES_INTERNAL_NO_WATER,
    MODES_4,
    SERVICE_TIME_DAYS,
    TEN_MINUTES_RESOLUTION,
)
from ..utils import venta_time_to_days_left, venta_time_to_minutes
from ..venta import VentaDataUpdateCoordinator
from ..venta_entity import (
    VentaBinarySensor,
    VentaBinarySensorEntityDescription,
    VentaLight,
    VentaSelect,
    VentaSelectEntityDescription,
    VentaSensor,
    VentaSensorEntityDescription,
    VentaV2HumidifierEntity,
)

WATER_WARNING = 1
ION_DISC_WARNING = 2
CLEANING_WARNING = 4
FILTER_WARNING = 8
SERVICE_WARNING = 16


async def async_setup_humidifier(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up humidifiers for Venta LW73."""
    async_add_entities(
        [VentaV2HumidifierEntity(coordinator, modes=[MODE_SLEEP, *MODES_4])]
    )


async def async_setup_binary_sensor(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors for Venta LW73."""
    descriptions = [
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_REFILL,
            translation_key=ATTR_NEEDS_REFILL,
            icon="mdi:water-alert",
            value_func=(lambda data: data.info.get("Warnings") & WATER_WARNING),
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_DISC_REPLACEMENT,
            translation_key=ATTR_NEEDS_DISC_REPLACEMENT,
            icon="mdi:disc-alert",
            value_func=lambda data: data.info.get("Warnings") & ION_DISC_WARNING,
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_CLEANING,
            translation_key=ATTR_NEEDS_CLEANING,
            icon="mdi:spray-bottle",
            value_func=lambda data: data.info.get("Warnings") & CLEANING_WARNING,
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_SERVICE,
            translation_key=ATTR_NEEDS_SERVICE,
            icon="mdi:account-wrench",
            value_func=(lambda data: data.info.get("Warnings") & SERVICE_WARNING),
        ),
    ]
    async_add_entities(
        [VentaBinarySensor(coordinator, description) for description in descriptions]
    )


async def async_setup_sensor(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors for Venta LW73."""
    descriptions = [
        VentaSensorEntityDescription(
            key=ATTR_DISC_ION_TIME_TO_REPLACE,
            translation_key=ATTR_DISC_ION_TIME_TO_REPLACE,
            icon="mdi:wrench-clock",
            native_unit_of_measurement=UnitOfTime.DAYS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_days_left(
                coordinator.data.info.get("DiscIonT"),
                ION_DISC_REPLACE_TIME_DAYS,
                FIVE_MINUTES_RESOLUTION,
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_TIME_TO_CLEAN,
            translation_key=ATTR_TIME_TO_CLEAN,
            icon="mdi:wrench-clock",
            native_unit_of_measurement=UnitOfTime.DAYS,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_days_left(
                coordinator.data.info.get("CleaningT"),
                CLEAN_TIME_DAYS,
                FIVE_MINUTES_RESOLUTION,
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
            key=ATTR_WATER_LEVEL,
            translation_key=ATTR_WATER_LEVEL,
            icon="mdi:water",
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: coordinator.data.measure.get("WaterLevel"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_FAN_SPEED,
            translation_key=ATTR_FAN_SPEED,
            native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
            icon="mdi:fast-forward",
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: coordinator.data.measure.get("FanRpm"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_OPERATION_TIME,
            translation_key=ATTR_OPERATION_TIME,
            icon="mdi:timer",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("OperationT"), FIVE_MINUTES_RESOLUTION
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_DISC_ION_TIME,
            translation_key=ATTR_DISC_ION_TIME,
            icon="mdi:timer",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("DiscIonT"), FIVE_MINUTES_RESOLUTION
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_CLEANING_TIME,
            translation_key=ATTR_CLEANING_TIME,
            icon="mdi:timer",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("CleaningT"), FIVE_MINUTES_RESOLUTION
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
    """Set up switches for Venta LW73."""
    pass


async def async_setup_light(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up lights for Venta LW73."""
    async_add_entities([VentaLight(coordinator)])


async def async_setup_select(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up selects for Venta LW73."""
    async_add_entities(
        [
            VentaSelect(
                coordinator,
                VentaSelectEntityDescription(
                    key=ATTR_LED_STRIP_MODE,
                    translation_key=ATTR_LED_STRIP_MODE,
                    entity_category=EntityCategory.CONFIG,
                    value_func=lambda data: str(data.action.get("LEDStripMode")),
                    action_func=(
                        lambda option: {"Action": {"LEDStripMode": int(option)}}
                    ),
                    options=[
                        LED_STRIP_MODES_INTERNAL,
                        LED_STRIP_MODES_INTERNAL_NO_WATER,
                        LED_STRIP_MODES_EXTERNAL,
                        LED_STRIP_MODES_EXTERNAL_NO_WATER,
                    ],
                ),
            )
        ]
    )
