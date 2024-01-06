"""Config flow for Venta integration."""
from __future__ import annotations

import logging
from typing import Any

import asyncio
import voluptuous as vol

from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_API_VERSION
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, TIMEOUT
from .venta import VentaDevice, VentaApiVersionError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Venta."""

    VERSION = 3

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                host = user_input[CONF_HOST]
                async with asyncio.timeout(TIMEOUT):
                    device = VentaDevice(host, None, async_get_clientsession(self.hass))
                    await device.detect_api_version()
                    await device.init()
            except (asyncio.TimeoutError, ClientError):
                _LOGGER.debug("Connection to %s timed out", host)
                errors["base"] = "cannot_connect"
            except VentaApiVersionError:
                _LOGGER.debug("Cannot detect the api version")
                errors["base"] = "cannot_detect_api_version"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return await self._create_entry(
                    device.host, device.api_version, device.mac
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def _create_entry(self, host, api_version, mac):
        """Register new entry."""
        if not self.unique_id:
            await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=host,
            data={CONF_HOST: host, CONF_API_VERSION: api_version, CONF_MAC: mac},
        )
