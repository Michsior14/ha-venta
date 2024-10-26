"""Support for Venta binary sensors."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CLEAN_MODE,
    ATTR_NEEDS_CLEANING,
    ATTR_NEEDS_DISC_REPLACEMENT,
    ATTR_NEEDS_FILTER_CLEANING,
    ATTR_NEEDS_REFILL,
    ATTR_NEEDS_SERVICE,
    CLEAN_TIME_DAYS,
    DOMAIN,
    FILTER_TIME_DAYS,
    ION_DISC_REPLACE_TIME_DAYS,
    NO_WATER_THRESHOLD,
    SERVICE_TIME_DAYS,
)
from .utils import needs_maintenance
from .venta import VentaDataUpdateCoordinator, VentaDeviceType
from .venta_entity import VentaBinarySensor, VentaBinarySensorEntityDescription


def _supported_sensors(
    device_type: VentaDeviceType,
) -> list[VentaBinarySensorEntityDescription]:
    """Return supported sensors for given device type."""
    common_service_warnings = [16, 17]
    common_sensors = [
        VentaBinarySensorEntityDescription(
            key=ATTR_NEEDS_REFILL,
            translation_key=ATTR_NEEDS_REFILL,
            icon="mdi:water-alert",
            value_func=(
                lambda data: data.info.get("Warnings") != 0
                and data.measure.get("WaterLevel") < NO_WATER_THRESHOLD
            ),
        ),
    ]
    match device_type:
        case VentaDeviceType.UNKNOWN:
            return [
                *common_sensors,
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_SERVICE,
                    translation_key=ATTR_NEEDS_SERVICE,
                    icon="mdi:account-wrench",
                    value_func=(
                        lambda data: data.info.get("Warnings")
                        in common_service_warnings
                    ),
                ),
            ]
        case VentaDeviceType.LW73_LW74:
            return [
                *common_sensors,
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_DISC_REPLACEMENT,
                    translation_key=ATTR_NEEDS_DISC_REPLACEMENT,
                    icon="mdi:disc-alert",
                    value_func=lambda data: needs_maintenance(
                        data.info.get("DiscIonT"), ION_DISC_REPLACE_TIME_DAYS
                    ),
                ),
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_CLEANING,
                    translation_key=ATTR_NEEDS_CLEANING,
                    icon="mdi:spray-bottle",
                    value_func=lambda data: needs_maintenance(
                        data.info.get("CleaningT"), CLEAN_TIME_DAYS
                    ),
                ),
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_SERVICE,
                    translation_key=ATTR_NEEDS_SERVICE,
                    icon="mdi:account-wrench",
                    value_func=(
                        lambda data: data.info.get("Warnings")
                        in common_service_warnings
                        or needs_maintenance(
                            data.info.get("ServiceT"), SERVICE_TIME_DAYS
                        )
                    ),
                ),
            ]
        case VentaDeviceType.LPH60:
            return [
                *common_sensors,
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_DISC_REPLACEMENT,
                    translation_key=ATTR_NEEDS_DISC_REPLACEMENT,
                    icon="mdi:disc-alert",
                    value_func=lambda data: needs_maintenance(
                        data.info.get("DiscIonT"), ION_DISC_REPLACE_TIME_DAYS
                    ),
                ),
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_CLEANING,
                    translation_key=ATTR_NEEDS_CLEANING,
                    icon="mdi:spray-bottle",
                    value_func=lambda data: needs_maintenance(
                        data.info.get("CleaningT"), CLEAN_TIME_DAYS
                    ),
                ),
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_SERVICE,
                    translation_key=ATTR_NEEDS_SERVICE,
                    icon="mdi:account-wrench",
                    value_func=(
                        lambda data: data.info.get("Warnings")
                        in common_service_warnings
                        or needs_maintenance(
                            data.info.get("ServiceT"), SERVICE_TIME_DAYS
                        )
                    ),
                ),
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_FILTER_CLEANING,
                    translation_key=ATTR_NEEDS_FILTER_CLEANING,
                    icon="mdi:filter",
                    value_func=lambda data: needs_maintenance(
                        data.info.get("FilterT"), FILTER_TIME_DAYS
                    ),
                ),
                VentaBinarySensorEntityDescription(
                    key=ATTR_CLEAN_MODE,
                    translation_key=ATTR_CLEAN_MODE,
                    icon="mdi:silverware-clean",
                    value_func=(lambda data: data.info.get("CleanMode")),
                ),
            ]
        case VentaDeviceType.AH550_AH555:
            return [
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_REFILL,
                    translation_key=ATTR_NEEDS_REFILL,
                    icon="mdi:water-alert",
                    value_func=(lambda data: data.info.get("Warnings") == 1),
                ),
                VentaBinarySensorEntityDescription(
                    key=ATTR_NEEDS_SERVICE,
                    translation_key=ATTR_NEEDS_SERVICE,
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
    ]
    async_add_entities(entities)
