"""Setup entity for Venta device."""

from __future__ import annotations

import logging
from typing import Literal

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.importlib import async_import_module

from .venta import VentaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_device(
    entity_type: Literal[
        "binary_sensor", "humidifier", "sensor", "switch", "light", "select"
    ],
    hass: HomeAssistant,
    coordinator: VentaDataUpdateCoordinator,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entities for specified Venta device."""
    device = coordinator.api.device.device_type.value
    module_path = f"custom_components.venta.devices.{device}"

    try:
        module = await async_import_module(hass, module_path)

        _LOGGER.debug("Setting up %s for module %s", entity_type, device)

        function_name = f"async_setup_{entity_type}"
        if not hasattr(module, function_name):
            _LOGGER.debug("Function %s not found in module %s", function_name, device)
            return

        await getattr(module, function_name)(coordinator, async_add_entities)
    except ImportError as error:
        _LOGGER.error("Unable to import module %s\n%s", module_path, error)
