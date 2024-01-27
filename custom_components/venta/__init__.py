"""The Venta integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from aiohttp import ClientConnectionError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_VERSION,
    CONF_HOST,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .config_flow import ConfigVersion
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .venta import VentaApi, VentaApiVersion, VentaDataUpdateCoordinator, VentaDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.HUMIDIFIER,
    Platform.SENSOR,
    Platform.LIGHT,
    Platform.SELECT,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Venta from a config entry."""
    conf = entry.data
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=conf[CONF_MAC])

    api = await venta_api_setup(
        hass,
        conf[CONF_HOST],
        timedelta(seconds=conf.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        conf[CONF_API_VERSION],
    )
    if not api:
        return False

    coordinator = VentaDataUpdateCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def venta_api_setup(
    hass: HomeAssistant, host: str, update_interval: timedelta, api_version: int
) -> VentaApi | None:
    """Create a Venta instance only once."""
    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(10):
            device = VentaDevice(host, update_interval, api_version, session)
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


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", entry.version)

    if entry.version == ConfigVersion.V1:
        new = {**entry.data, CONF_API_VERSION: VentaApiVersion.V2.value}
        entry.version = ConfigVersion.V2
        hass.config_entries.async_update_entry(entry, data=new)
    if entry.version == ConfigVersion.V2:
        entry.version = ConfigVersion.V3
        hass.config_entries.async_update_entry(entry)

    _LOGGER.debug("Migration to version %s successful", entry.version)

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)
