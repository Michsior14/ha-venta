"""Venta AP902 setup functions."""

from __future__ import annotations

from homeassistant.components.humidifier.const import MODE_SLEEP
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import (
    ATTR_CHILD_LOCK,
    ATTR_FAN_SPEED,
    ATTR_FILTER_TIME,
    ATTR_HEPA_FILTER_LIFETIME,
    ATTR_HUMIDITY,
    ATTR_NEEDS_FILTER_CLEANING,
    ATTR_OPERATION_TIME,
    ATTR_PM_2_5,
    ATTR_TIMER,
    ATTR_TIMER_TIME,
    ATTR_WARNINGS,
    ATTR_WATER_LEVEL,
    FIVE_MINUTES_RESOLUTION,
    MODES_5,
    ONE_MINUTE_RESOLUTION,
    TEN_MINUTES_RESOLUTION,
    TIMER_MODES_1H,
    TIMER_MODES_3H,
    TIMER_MODES_5H,
    TIMER_MODES_7H,
    TIMER_MODES_9H,
    TIMER_MODES_OFF,
    WATER_LEVEL_NO_VALUE,
    WATER_LEVEL_OK,
    WATER_LEVEL_OVERFLOW,
    WATER_LEVEL_RED,
    WATER_LEVEL_YELLOW,
)
from ..utils import venta_time_to_minutes
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

FILTER_WARNING = 16

# TODO:  Add timer selection


async def async_setup_humidifier(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up humidifiers for Venta AP902."""
    async_add_entities(
        [VentaV0HumidifierEntity(coordinator, modes=[MODE_SLEEP, *MODES_5])]
    )


async def async_setup_binary_sensor(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors for Venta AP902."""
    descriptions = [
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_FILTER_CLEANING,
            translation_key=ATTR_NEEDS_FILTER_CLEANING,
            icon="mdi:air-filter",
            value_func=(lambda data: data.info.get("Warnings") & FILTER_WARNING),
        ),
    ]
    async_add_entities(
        [VentaBinarySensor(coordinator, description) for description in descriptions]
    )


async def async_setup_sensor(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors for Venta AP902."""
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
            key=ATTR_PM_2_5,
            translation_key=ATTR_PM_2_5,
            device_class=SensorDeviceClass.PM25,
            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: coordinator.data.measure.get("Dust"),
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
        VentaSensorEntityDescription(
            key=ATTR_HEPA_FILTER_LIFETIME,
            translation_key=ATTR_HEPA_FILTER_LIFETIME,
            icon="mdi:air-filter",
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_func=lambda coordinator: venta_time_to_minutes(
                coordinator.data.action.get("FiltLifetime"),
                TEN_MINUTES_RESOLUTION,
            ),
        ),
    ]
    async_add_entities(
        [VentaSensor(coordinator, description) for description in descriptions]
    )


async def async_setup_switch(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up switches for Venta AP902."""
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
    """Set up lights for Venta AP902."""
    pass


async def async_setup_select(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up selects for Venta AP902."""
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
                    action_func=(lambda option: {"Action": {"Timer": int(option)}}),
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
