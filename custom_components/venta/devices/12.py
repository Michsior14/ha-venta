"""Venta AH902 setup functions."""

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
    ATTR_CHILD_LOCK,
    ATTR_CLEAN_MODE,
    ATTR_DISC_ION_TIME_TO_REPLACE,
    ATTR_DOOR_OPEN,
    ATTR_FAN_SPEED,
    ATTR_FILTER_TIME,
    ATTR_HUMIDITY,
    ATTR_NEEDS_CLEANING,
    ATTR_NEEDS_DISC_REPLACEMENT,
    ATTR_NEEDS_FILTER_CLEANING,
    ATTR_NEEDS_REFILL,
    ATTR_NEEDS_REFILL_SOON,
    ATTR_NEEDS_SERVICE,
    ATTR_OPERATION_TIME,
    ATTR_REMAINING_CLEANING_TIME,
    ATTR_SERVICE_TIME,
    ATTR_TIME_TO_CLEAN,
    ATTR_TIMER_TIME,
    ATTR_UVC_LAMP_OFF_TIME,
    ATTR_UVC_LAMP_ON_TIME,
    ATTR_WARNINGS,
    ATTR_WATER_LEVEL,
    CLEAN_TIME_DAYS,
    FIVE_MINUTES_RESOLUTION,
    ION_DISC_REPLACE_TIME_DAYS,
    MODES_5,
    ONE_MINUTE_RESOLUTION,
    TEN_MINUTES_RESOLUTION,
    WATER_LEVEL_NO_VALUE,
    WATER_LEVEL_OK,
    WATER_LEVEL_RED,
    WATER_LEVEL_YELLOW,
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
    VentaV0HumidifierEntity,
)

FILL_TANK_RED_WARNING = 1
FILL_TANK_YELLOW_WARNING = 2
CLOSE_DOOR_WARNING = 4
FILTER_WARNING = 16
ION_DISC_WARNING = 32
CLEANING_WARNING = 64
SERVICE_WARNING = 256

# TODO:  Add timer selection


async def async_setup_humidifier(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up humidifiers for Venta AH902."""
    async_add_entities(
        [VentaV0HumidifierEntity(coordinator, modes=[MODE_SLEEP, *MODES_5])]
    )


async def async_setup_binary_sensor(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors for Venta AH902."""
    descriptions = [
        VentaBinarySensorEntityDescription(
            key=ATTR_CLEAN_MODE,
            translation_key=ATTR_CLEAN_MODE,
            icon="mdi:silverware-clean",
            value_func=(lambda data: data.info.get("CleanMode")),
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_REFILL,
            translation_key=ATTR_NEEDS_REFILL,
            icon="mdi:water-alert",
            value_func=(lambda data: data.info.get("Warnings") & FILL_TANK_RED_WARNING),
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_REFILL_SOON,
            translation_key=ATTR_NEEDS_REFILL_SOON,
            icon="mdi:water-alert",
            value_func=(
                lambda data: data.info.get("Warnings") & FILL_TANK_YELLOW_WARNING
            ),
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_DOOR_OPEN,
            translation_key=ATTR_DOOR_OPEN,
            icon="mdi:door-open",
            value_func=(lambda data: data.info.get("Warnings") & CLOSE_DOOR_WARNING),
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_FILTER_CLEANING,
            translation_key=ATTR_NEEDS_FILTER_CLEANING,
            icon="mdi:air-filter",
            value_func=(lambda data: data.info.get("Warnings") & FILTER_WARNING),
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
    """Set up sensors for Venta AH902."""
    descriptions = [
        VentaSensorEntityDescription(
            key=ATTR_TIMER_TIME,
            translation_key=ATTR_TIMER_TIME,
            icon="mdi:timer",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("TimerT"), ONE_MINUTE_RESOLUTION
            ),
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
            key=ATTR_FILTER_TIME,
            translation_key=ATTR_FILTER_TIME,
            icon="mdi:timer",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("FilterT"), TEN_MINUTES_RESOLUTION
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_SERVICE_TIME,
            translation_key=ATTR_SERVICE_TIME,
            icon="mdi:timer",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("ServiceT"), FIVE_MINUTES_RESOLUTION
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_UVC_LAMP_ON_TIME,
            translation_key=ATTR_UVC_LAMP_ON_TIME,
            icon="mdi:lightbulb-on",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("UVCOnT"),
                ONE_MINUTE_RESOLUTION,
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_UVC_LAMP_OFF_TIME,
            translation_key=ATTR_UVC_LAMP_OFF_TIME,
            icon="mdi:lightbulb-off",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("UVCOffT"),
                ONE_MINUTE_RESOLUTION,
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_REMAINING_CLEANING_TIME,
            translation_key=ATTR_REMAINING_CLEANING_TIME,
            icon="mdi:timer",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.info.get("CleaningR"), ONE_MINUTE_RESOLUTION
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
            device_class=SensorDeviceClass.ENUM,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            options=[
                WATER_LEVEL_NO_VALUE,
                WATER_LEVEL_YELLOW,
                WATER_LEVEL_RED,
                WATER_LEVEL_OK,
            ],
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
    """Set up switches for Venta AH902."""
    descriptions = [
        VentaSwitchEntityDescription(
            key=ATTR_CHILD_LOCK,
            translation_key=ATTR_CHILD_LOCK,
            entity_category=EntityCategory.CONFIG,
            value_func=lambda data: data.action.get("ChildLock"),
            action_func=(
                lambda _, is_on: (
                    {
                        "ChildLock": is_on,
                        "Action": "control",
                    }
                )
            ),
        ),
    ]
    async_add_entities(
        [VentaSwitch(coordinator, description) for description in descriptions]
    )


async def async_setup_light(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up lights for Venta AH902."""
    pass


async def async_setup_select(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up selects for Venta AH902."""
    pass
