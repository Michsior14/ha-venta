"""The Venta integration."""
from __future__ import annotations

import asyncio
import logging

from aiohttp import ClientConnectionError

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_API_VERSION

from .const import DOMAIN, TIMEOUT

from .venta import VentaApi, VentaDevice, VentaDataUpdateCoordinator, ApiVersion

_LOGGER = logging.getLogger(__name__)

SYNC_INTERVAL = 15

PLATFORMS: list[Platform] = [
    Platform.HUMIDIFIER,
    Platform.SENSOR,
    Platform.LIGHT,
    Platform.SELECT,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Venta from a config entry."""
    conf = entry.data
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=conf[CONF_MAC])

    api = await venta_api_setup(hass, conf[CONF_HOST], conf[CONF_API_VERSION])
    if not api:
        return False

    coordinator = VentaDataUpdateCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def venta_api_setup(hass: HomeAssistant, host, api_version):
    """Create a Venta instance only once."""
    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(TIMEOUT):
            device = VentaDevice(host, api_version, session)
            await device.init()
    except asyncio.TimeoutError as err:
        _LOGGER.debug("Connection to %s timed out", host)
        raise ConfigEntryNotReady from err
    except ClientConnectionError as err:
        _LOGGER.debug("ClientConnectionError to %s", host)
        raise ConfigEntryNotReady from err
    except Exception:  # pylint: disable=broad-except
        _LOGGER.error("Unexpected error creating device %s", host)
        return None

    api = VentaApi(device)

    return api


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version == 1:
        new = {**entry.data, CONF_API_VERSION: ApiVersion.V2.value}
        entry.version = 2
        hass.config_entries.async_update_entry(entry, data=new)

    _LOGGER.debug("Migration to version %s successful", entry.version)

    return True
