"""Config flow for Venta integration."""
from __future__ import annotations

import logging
from typing import Any

import asyncio
import voluptuous as vol

from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_HOST, CONF_MAC
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, TIMEOUT
from .venta import VentaDevice

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Venta."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                host = user_input[CONF_HOST]
                async with asyncio.timeout(TIMEOUT):
                    device = VentaDevice(host, async_get_clientsession(self.hass))
                    await device.init()
            except (asyncio.TimeoutError, ClientError):
                _LOGGER.debug("Connection to %s timed out", host)
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return await self._create_entry(device.host, device.mac)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def _create_entry(self, host, mac):
        """Register new entry."""
        if not self.unique_id:
            await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=host,
            data={CONF_HOST: host, CONF_MAC: mac},
        )
