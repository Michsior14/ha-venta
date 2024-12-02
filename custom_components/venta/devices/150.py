"""Venta AS150 setup functions."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.venta.utils import skip_zeros

from ..const import (
    ATTR_CO2,
    ATTR_HCHO,
    ATTR_HUMIDITY,
    ATTR_PARTICLES_0_3,
    ATTR_PARTICLES_0_5,
    ATTR_PARTICLES_10,
    ATTR_PARTICLES_2_5,
    ATTR_PARTICLES_5_0,
    ATTR_PM_1_0,
    ATTR_PM_2_5,
    ATTR_PM_10,
    ATTR_TOLUENE,
    ATTR_VOC,
)
from ..venta import VentaDataUpdateCoordinator
from ..venta_entity import (
    VentaSensor,
    VentaSensorEntityDescription,
)

# TODO:  Check how SensorStatus works e.g. "0000001F"


async def async_setup_humidifier(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up humidifiers for Venta AS150."""
    pass


async def async_setup_binary_sensor(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors for Venta AS150."""
    pass


async def async_setup_sensor(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors for Venta AS150."""
    descriptions = [
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
            key=ATTR_CO2,
            translation_key=ATTR_CO2,
            device_class=SensorDeviceClass.CO2,
            native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: skip_zeros(
                coordinator.data.measure.get("Co2")
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_VOC,
            translation_key=ATTR_VOC,
            device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: skip_zeros(
                coordinator.data.measure.get("Voc"),
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_TOLUENE,
            translation_key=ATTR_TOLUENE,
            device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: coordinator.data.measure.get("Toluene"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_HCHO,
            translation_key=ATTR_HCHO,
            native_unit_of_measurement=CONCENTRATION_PARTS_PER_BILLION,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: skip_zeros(
                coordinator.data.measure.get("Hcho")
            ),
        ),
        VentaSensorEntityDescription(
            key=ATTR_PM_1_0,
            translation_key=ATTR_PM_1_0,
            device_class=SensorDeviceClass.PM1,
            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: coordinator.data.measure.get("PmCalc1u0")
            or coordinator.data.measure.get("Pm1u0"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_PM_2_5,
            translation_key=ATTR_PM_2_5,
            device_class=SensorDeviceClass.PM25,
            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: coordinator.data.measure.get("PmCalc2u5")
            or coordinator.data.measure.get("Pm2u5"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_PM_10,
            translation_key=ATTR_PM_10,
            device_class=SensorDeviceClass.PM10,
            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: coordinator.data.measure.get("PmCalc10u")
            or coordinator.data.measure.get("Pm10u"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_PARTICLES_0_3,
            translation_key=ATTR_PARTICLES_0_3,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: coordinator.data.measure.get("Particles0u3"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_PARTICLES_0_5,
            translation_key=ATTR_PARTICLES_0_5,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: coordinator.data.measure.get("Particles0u5"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_PARTICLES_2_5,
            translation_key=ATTR_PARTICLES_2_5,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: coordinator.data.measure.get("Particles2u5"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_PARTICLES_5_0,
            translation_key=ATTR_PARTICLES_5_0,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: coordinator.data.measure.get("Particles5u0"),
        ),
        VentaSensorEntityDescription(
            key=ATTR_PARTICLES_10,
            translation_key=ATTR_PARTICLES_10,
            state_class=SensorStateClass.MEASUREMENT,
            value_func=lambda coordinator: coordinator.data.measure.get("Particles10u"),
        ),
    ]
    async_add_entities(
        [VentaSensor(coordinator, description) for description in descriptions]
    )


async def async_setup_switch(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up switches for Venta AS150."""
    pass


async def async_setup_light(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up lights for Venta AS150."""
    pass


async def async_setup_select(
    coordinator: VentaDataUpdateCoordinator, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up selects for Venta AS150."""
    pass
