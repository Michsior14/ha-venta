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
    ATTR_TEMPERATURE,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CLEANING_TIME,
    ATTR_CO2,
    ATTR_DISC_ION_TIME,
    ATTR_DISC_ION_TIME_TO_REPLACE,
    ATTR_FAN_SPEED,
    ATTR_HCHO,
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
    ATTR_CLEANING,
    ATTR_HUMIDITY,
    DOMAIN,
    CLEAN_TIME_DAYS,
    FILTER_TIME_DAYS,
    ION_DISC_REPLACE_TIME_DAYS,
    SERVICE_TIME_DAYS,
)
from .utils import skip_zeros, venta_time_to_days_left, venta_time_to_minutes
from .venta import VentaDataUpdateCoordinator, VentaDeviceType


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


SENSOR_TYPES: list[VentaSensorEntityDescription] = (
    # LW73/LW74 only sensors
    VentaSensorEntityDescription(
        key=ATTR_DISC_ION_TIME_TO_REPLACE,
        translation_key="disc_ion_time_to_replace",
        icon="mdi:power-settings",
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: (
            coordinator.api.device.device_type in [VentaDeviceType.LW73_LW74, VentaDeviceType.LPH60]
            and coordinator.data.info.get("DiscIonT") is not None
        ),
        value_func=lambda coordinator: venta_time_to_days_left(
            coordinator.data.info.get("DiscIonT"),
            ION_DISC_REPLACE_TIME_DAYS,
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_TIME_TO_CLEAN,
        translation_key="time_to_clean",
        icon="mdi:power-settings",
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: (
            coordinator.api.device.device_type in [VentaDeviceType.LW73_LW74, VentaDeviceType.LPH60, VentaDeviceType.LW60]
            and coordinator.data.info.get("FilterT") is not None
        ),
        value_func=lambda coordinator: venta_time_to_days_left(
            coordinator.data.info.get("FilterT"), FILTER_TIME_DAYS
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_TIME_TO_CLEAN,
        translation_key="time_to_clean",
        icon="mdi:power-settings",
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: (
            coordinator.api.device.device_type in [VentaDeviceType.LW73_LW74, VentaDeviceType.LPH60, VentaDeviceType.LW60]
            and coordinator.data.info.get("CleaningT") is not None
        ),
        value_func=lambda coordinator: venta_time_to_days_left(
            coordinator.data.info.get("CleaningT"), CLEAN_TIME_DAYS
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_TIME_TO_SERVICE,
        translation_key="time_to_service",
        icon="mdi:power-settings",
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: (
            coordinator.api.device.device_type in [VentaDeviceType.LW73_LW74, VentaDeviceType.LPH60, VentaDeviceType.LW60]
            and coordinator.data.info.get("ServiceT") is not None
        ),
        value_func=lambda coordinator: venta_time_to_days_left(
            coordinator.data.info.get("ServiceT"), SERVICE_TIME_DAYS
        ),
    ),
    # All sensors
    VentaSensorEntityDescription(
        key=ATTR_TEMPERATURE,
        translation_key="temperature",
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
        translation_key="humidity",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.HUMIDITY,
        suggested_display_precision=1,
        exists_func=lambda coordinator: coordinator.data.measure.get("Humidity")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Humidity"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_WATER_LEVEL,
        translation_key="water_level",
        icon="mdi:water",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.measure.get("WaterLevel")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("WaterLevel"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PARTICLES_2_5,
        translation_key="particles_2_5",
        icon="mdi:molecule",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        exists_func=lambda coordinator: coordinator.data.measure.get("Dust")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Dust"),
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
        value_func=lambda coordinator: coordinator.data.measure.get("FanRpm"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_OPERATION_TIME,
        translation_key="operation_time",
        icon="mdi:timelapse",
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
        translation_key="disc_ion_time",
        icon="mdi:timelapse",
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
        translation_key="cleaning_time",
        icon="mdi:timelapse",
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
        translation_key="service_time",
        icon="mdi:wrench-clock",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("ServiceT")
        is not None,
        value_func=lambda coordinator: venta_time_to_minutes(
            coordinator.data.info.get("ServiceT")
        ),
    ),
    VentaSensorEntityDescription(
        key=ATTR_SERVICE_MAX_TIME,
        translation_key="service_max_time",
        icon="mdi:power-settings",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("ServiceMax")
        is not None,
        value_func=lambda coordinator: coordinator.data.info.get("ServiceMax"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_WARNINGS,
        translation_key="warnings",
        icon="mdi:alert",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_func=lambda coordinator: coordinator.data.info.get("Warnings")
        is not None,
        value_func=lambda coordinator: coordinator.data.info.get("Warnings"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PARTICLES_0_3,
        translation_key="particles_0_3",
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Particles0u3")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Particles0u3"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PARTICLES_0_5,
        translation_key="particles_0_5",
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Particles0u5")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Particles0u5"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PARTICLES_2_5,
        translation_key="particles_2_5",
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Particles2u5")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Particles2u5"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PARTICLES_5_0,
        translation_key="particles_5_0",
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Particles5u0")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Particles5u0"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PARTICLES_10,
        translation_key="particles_10",
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("Particles10u")
        is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("Particles10u"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PM_1_0,
        translation_key="pm_1_0",
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
        translation_key="pm_2_5",
        device_class=SensorDeviceClass.PM25,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        exists_func=lambda coordinator: coordinator.data.measure.get("PmCalc2u5")
        is not None
        or coordinator.data.measure.get("Pm2u5") is not None,
        value_func=lambda coordinator: coordinator.data.measure.get("PmCalc2u5")
        or coordinator.data.measure.get("Pm2u5"),
    ),
    VentaSensorEntityDescription(
        key=ATTR_PM_10,
        translation_key="pm_10",
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
        translation_key="co2",
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
        translation_key="voc_index",
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
        translation_key="hcho",
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
