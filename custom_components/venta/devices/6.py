"""Venta LW62T setup functions."""

from __future__ import annotations

from homeassistant.components.humidifier.const import MODE_SLEEP
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfTime,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import (
    ATTR_CHILD_LOCK,
    ATTR_CLEAN_MODE,
    ATTR_DISC_ION_TIME_TO_REPLACE,
    ATTR_DISC_RELAY,
    ATTR_DOOR_OPEN,
    ATTR_FAN_RELAY,
    ATTR_FAN_SPEED,
    ATTR_HUMIDITY,
    ATTR_NEEDS_CLEANING,
    ATTR_NEEDS_DISC_REPLACEMENT,
    ATTR_NEEDS_FILTER_CLEANING,
    ATTR_NEEDS_REFILL,
    ATTR_NEEDS_REFILL_SOON,
    ATTR_OPERATION_TIME,
    ATTR_REMAINING_CLEANING_TIME,
    ATTR_TIME_TO_CLEAN,
    ATTR_TIMER,
    ATTR_TIMER_TIME,
    ATTR_UVC_LAMP_OFF_TIME,
    ATTR_UVC_LAMP_ON_TIME,
    ATTR_UVC_RELAY,
    ATTR_VALVE_RELAY,
    ATTR_WARNINGS,
    ATTR_WATER_LEVEL,
    CLEAN_TIME_DAYS,
    FIVE_MINUTES_RESOLUTION,
    ION_DISC_REPLACE_TIME_DAYS,
    MODES_5,
    ONE_MINUTE_RESOLUTION,
    TIMER_MODES_1H,
    TIMER_MODES_3H,
    TIMER_MODES_5H,
    TIMER_MODES_7H,
    TIMER_MODES_9H,
    TIMER_MODES_OFF,
    WATER_LEVEL_NO_VALUE,
    WATER_LEVEL_OK,
    WATER_LEVEL_RED,
    WATER_LEVEL_YELLOW,
    WATER_LEVEL_OVERFLOW,
)
from ..utils import (
    get_from_list,
    venta_temperature_unit,
    venta_time_to_days_left,
    venta_time_to_minutes,
)
from ..venta import VentaDataUpdateCoordinator
from ..venta_entity import (
    VentaBinarySensor,
    VentaBinarySensorEntityDescription,
    VentaSelect,
    VentaSelectEntityDescription,
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


async def async_setup_humidifier(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up humidifiers for Venta LW62T."""
    async_add_entities(
        [VentaV0HumidifierEntity(coordinator, modes=[MODE_SLEEP, *MODES_5])]
    )


async def async_setup_binary_sensor(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors for Venta LW62T."""
    descriptions = [
        VentaBinarySensorEntityDescription(
            key=ATTR_CLEAN_MODE,
            translation_key=ATTR_CLEAN_MODE,
            icon="mdi:silverware-clean",
            value_func=lambda data: data.info.get("CleanMode"),
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_FAN_RELAY,
            translation_key=ATTR_FAN_RELAY,
            icon="mdi:electric-switch",
            value_func=lambda data: get_from_list(data.info.get("RelState"), 0),
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_DISC_RELAY,
            translation_key=ATTR_DISC_RELAY,
            icon="mdi:electric-switch",
            value_func=lambda data: get_from_list(data.info.get("RelState"), 1),
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_UVC_RELAY,
            translation_key=ATTR_UVC_RELAY,
            icon="mdi:electric-switch",
            value_func=lambda data: get_from_list(data.info.get("RelState"), 2),
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_VALVE_RELAY,
            translation_key=ATTR_VALVE_RELAY,
            icon="mdi:electric-switch",
            value_func=lambda data: get_from_list(data.info.get("RelState"), 3),
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_REFILL,
            translation_key=ATTR_NEEDS_REFILL,
            icon="mdi:water-alert",
            value_func=lambda data: data.info.get("Warnings") & FILL_TANK_RED_WARNING,
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
            icon="mdi:door-closed",
            value_func=lambda data: data.info.get("Warnings") & CLOSE_DOOR_WARNING,
        ),
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_FILTER_CLEANING,
            translation_key=ATTR_NEEDS_FILTER_CLEANING,
            icon="mdi:air-filter",
            value_func=lambda data: data.info.get("Warnings") & FILTER_WARNING,
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
    ]
    async_add_entities(
        [VentaBinarySensor(coordinator, description) for description in descriptions]
    )


async def async_setup_sensor(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors for Venta LW62T."""
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
            suggested_display_precision=1,
            value_func=lambda coordinator: coordinator.data.measure.get("Temperature"),
            unit_func=lambda coordinator: venta_temperature_unit(
                coordinator.data.action.get("TempUnit")
            ),
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
            entity_category=EntityCategory.DIAGNOSTIC,
            options=[
                WATER_LEVEL_NO_VALUE,
                WATER_LEVEL_YELLOW,
                WATER_LEVEL_RED,
                WATER_LEVEL_OK,
                WATER_LEVEL_OVERFLOW,
            ],
            value_func=lambda coordinator: (
                str(coordinator.data.measure.get("WaterLevel"))
                if coordinator.data.measure.get("WaterLevel") is not None
                else None
            ),
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
    """Set up switches for Venta LW62T."""
    descriptions = [
        VentaSwitchEntityDescription(
            key=ATTR_CHILD_LOCK,
            translation_key=ATTR_CHILD_LOCK,
            entity_category=EntityCategory.CONFIG,
            value_func=lambda data: data.action.get("ChildLock"),
            action_func=lambda _, is_on: {
                "ChildLock": is_on,
                "Action": "control",
            },
        ),
    ]
    async_add_entities(
        [VentaSwitch(coordinator, description) for description in descriptions]
    )


async def async_setup_light(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up lights for Venta LW62T."""
    pass


async def async_setup_select(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up selects for Venta LW62T."""
    async_add_entities(
        [
            VentaSelect(
                coordinator,
                VentaSelectEntityDescription(
                    key=ATTR_TIMER,
                    translation_key=ATTR_TIMER,
                    entity_category=EntityCategory.CONFIG,
                    value_func=lambda data: (
                        str(data.action.get("Timer"))
                        if data.action.get("Timer")
                        else None
                    ),
                    action_func=lambda option: {"Action": {"Timer": int(option)}},
                    options=[
                        TIMER_MODES_OFF,
                        TIMER_MODES_1H,
                        TIMER_MODES_3H,
                        TIMER_MODES_5H,
                        TIMER_MODES_7H,
                        TIMER_MODES_9H,
                    ],
                ),
            )
        ]
    )
