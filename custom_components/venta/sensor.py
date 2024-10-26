"""Support for Venta sensors."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CLEANING_TIME,
    ATTR_CO2,
    ATTR_DISC_ION_TIME,
    ATTR_DISC_ION_TIME_TO_REPLACE,
    ATTR_FAN_SPEED,
    ATTR_FILTER_TIME,
    ATTR_FILTER_TIME_TO_CLEAN,
    ATTR_HCHO,
    ATTR_HUMIDITY,
    ATTR_OPERATION_TIME,
    ATTR_PARTICLES_0_3,
    ATTR_PARTICLES_0_5,
    ATTR_PARTICLES_2_5,
    ATTR_PARTICLES_5_0,
    ATTR_PARTICLES_10,
    ATTR_PM_1_0,
    ATTR_PM_2_5,
    ATTR_PM_10,
    ATTR_SERVICE_MAX_TIME,
    ATTR_SERVICE_TIME,
    ATTR_TIME_TO_CLEAN,
    ATTR_TIME_TO_SERVICE,
    ATTR_VOC,
    ATTR_WARNINGS,
    ATTR_WATER_LEVEL,
    CLEAN_TIME_DAYS,
    DOMAIN,
    FILTER_TIME_DAYS,
    ION_DISC_REPLACE_TIME_DAYS,
    SERVICE_TIME_DAYS,
)
from .utils import (
    VentaTimeResolution,
    skip_zeros,
    venta_time_to_days_left,
    venta_time_to_minutes,
)
from .venta import VentaDataUpdateCoordinator, VentaDeviceType
from .venta_entity import VentaSensor, VentaSensorEntityDescription

SENSOR_TYPES: list[VentaSensorEntityDescription] = (
    # Time sensors
    VentaSensorEntityDescription(
        key=ATTR_DISC_ION_TIME_TO_REPLACE,
        translation_key=ATTR_DISC_ION_TIME_TO_REPLACE,
        icon="mdi:wrench-clock",
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: (
            coordinator.data.info.get("DiscIonT") is not None
        ),
        value_func=lambda coordinator: venta_time_to_days_left(
            coordinator.data.info.get("DiscIonT"),
            ION_DISC_REPLACE_TIME_DAYS,
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_FILTER_TIME_TO_CLEAN,
        translation_key=ATTR_FILTER_TIME_TO_CLEAN,
        icon="mdi:wrench-clock",
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: (
            # Skip LW73 and LW74 devices because they always report 0 values
            coordinator.api.device.device_type != VentaDeviceType.LW73_LW74
            and coordinator.data.info.get("FilterT") is not None
        ),
        value_func=lambda coordinator: venta_time_to_days_left(
            coordinator.data.info.get("FilterT"), FILTER_TIME_DAYS
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_TIME_TO_CLEAN,
        translation_key=ATTR_TIME_TO_CLEAN,
        icon="mdi:wrench-clock",
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: (
            coordinator.data.info.get("CleaningT") is not None
        ),
        value_func=lambda coordinator: venta_time_to_days_left(
            coordinator.data.info.get("CleaningT"), CLEAN_TIME_DAYS
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_TIME_TO_SERVICE,
        translation_key=ATTR_TIME_TO_SERVICE,
        icon="mdi:wrench-clock",
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: (
            coordinator.data.info.get("ServiceT") is not None
        ),
        value_func=lambda coordinator: venta_time_to_days_left(
            coordinator.data.info.get("ServiceT"),
            SERVICE_TIME_DAYS,
            VentaTimeResolution.SERVICE_TIME,
        ),
    ),
    # All other sensors
    VentaSensorEntityDescription(
        key=ATTR_TEMPERATURE,
        translation_key=ATTR_TEMPERATURE,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        exists_func=lambda coordinator: coordinator.data.measure.get("Temperature")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Temperature"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_HUMIDITY,
        translation_key=ATTR_HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        exists_func=lambda coordinator: coordinator.data.measure.get("Humidity")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Humidity"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_WATER_LEVEL,
        translation_key=ATTR_WATER_LEVEL,
        icon="mdi:water",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.measure.get("WaterLevel")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("WaterLevel"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_FAN_SPEED,
        translation_key=ATTR_FAN_SPEED,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        icon="mdi:fast-forward",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.measure.get("FanRpm")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("FanRpm"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_OPERATION_TIME,
        translation_key=ATTR_OPERATION_TIME,
        icon="mdi:timer",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("OperationT")
        is not None,
        value_func=lambda coordinator: venta_time_to_minutes(
            coordinator.data.info.get("OperationT")
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_DISC_ION_TIME,
        translation_key=ATTR_DISC_ION_TIME,
        icon="mdi:timer",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("DiscIonT")
        is not None,
        value_func=lambda coordinator: venta_time_to_minutes(
            coordinator.data.info.get("DiscIonT")
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_CLEANING_TIME,
        translation_key=ATTR_CLEANING_TIME,
        icon="mdi:timer",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("CleaningT")
        is not None,
        value_func=lambda coordinator: venta_time_to_minutes(
            coordinator.data.info.get("CleaningT")
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_SERVICE_TIME,
        translation_key=ATTR_SERVICE_TIME,
        icon="mdi:timer",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("ServiceT")
        is not None,
        value_func=lambda coordinator: venta_time_to_minutes(
            coordinator.data.info.get("ServiceT"),
            VentaTimeResolution.SERVICE_TIME,
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_SERVICE_MAX_TIME,
        translation_key=ATTR_SERVICE_MAX_TIME,
        icon="mdi:timer",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("ServiceMax")
        is not None,
        value_func=lambda coordinator: venta_time_to_minutes(
            coordinator.data.info.get("ServiceMax"),
            VentaTimeResolution.SERVICE_TIME,
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_FILTER_TIME,
        translation_key=ATTR_FILTER_TIME,
        icon="mdi:timer",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        # Skip LW73 and LW74 devices because they always report 0 values
        exists_func=lambda coordinator: coordinator.api.device.device_type
        != VentaDeviceType.LW73_LW74
        and coordinator.data.info.get("FilterT") is not None,
        value_func=lambda coordinator: venta_time_to_minutes(
            coordinator.data.info.get("FilterT")
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_WARNINGS,
        translation_key=ATTR_WARNINGS,
        icon="mdi:alert",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("Warnings")
        is not None,
        value_func=lambda coordinator: coordinator.data.info.get("Warnings"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PARTICLES_0_3,
        translation_key=ATTR_PARTICLES_0_3,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Particles0u3")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Particles0u3"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PARTICLES_0_5,
        translation_key=ATTR_PARTICLES_0_5,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Particles0u5")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Particles0u5"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PARTICLES_2_5,
        translation_key=ATTR_PARTICLES_2_5,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Particles2u5")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Particles2u5"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PARTICLES_5_0,
        translation_key=ATTR_PARTICLES_5_0,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Particles5u0")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Particles5u0"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PARTICLES_10,
        translation_key=ATTR_PARTICLES_10,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Particles10u")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Particles10u"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PM_1_0,
        translation_key=ATTR_PM_1_0,
        device_class=SensorDeviceClass.PM1,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("PmCalc1u0")
        is not None
        or coordinator.data.measure.get("Pm1u0") is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("PmCalc1u0")
        or coordinator.data.measure.get("Pm1u0"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PM_2_5,
        translation_key=ATTR_PM_2_5,
        device_class=SensorDeviceClass.PM25,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("PmCalc2u5")
        is not None
        or coordinator.data.measure.get("Pm2u5") is not None
        or (
            # Skip LW73 and LW74 devices because they always report 0 values
            coordinator.api.device.device_type != VentaDeviceType.LW73_LW74
            and coordinator.data.measure.get("Dust") is not None
        ),
        value_func=lambda coordinator: coordinator.data.measure.get("PmCalc2u5")
        or coordinator.data.measure.get("Pm2u5")
        or coordinator.data.measure.get("Dust"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PM_10,
        translation_key=ATTR_PM_10,
        device_class=SensorDeviceClass.PM10,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("PmCalc10u")
        is not None
        or coordinator.data.measure.get("Pm10u") is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("PmCalc10u")
        or coordinator.data.measure.get("Pm10u"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_CO2,
        translation_key=ATTR_CO2,
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Co2") is not None,
        value_func=lambda coordinator: skip_zeros(
            coordinator.data.measure.get("Co2"),
            coordinator,
            [VentaDeviceType.AS150],
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_VOC,
        translation_key=ATTR_VOC,
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Voc") is not None,
        value_func=lambda coordinator: skip_zeros(
            coordinator.data.measure.get("Voc"),
            coordinator,
            [VentaDeviceType.AS150],
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_HCHO,
        translation_key=ATTR_HCHO,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_BILLION,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Hcho")
        is not None,
        value_func=lambda coordinator: skip_zeros(
            coordinator.data.measure.get("Hcho"),
            coordinator,
            [VentaDeviceType.AS150],
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Venta sensors on config_entry."""
    coordinator: VentaDataUpdateCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    entities = [
        VentaSensor(coordinator, description)
        for description in SENSOR_TYPES
        if description.exists_func(coordinator)
    ]
    async_add_entities(entities)
