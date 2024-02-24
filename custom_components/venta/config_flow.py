"""Config flow for Venta integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from enum import IntEnum
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_VERSION,
    CONF_HOST,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
)
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import AUTO_API_VERSION, DEFAULT_SCAN_INTERVAL, DOMAIN
from .venta import VentaApiVersion, VentaApiVersionError, VentaDevice

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(
            CONF_API_VERSION, default=AUTO_API_VERSION
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    AUTO_API_VERSION,
                    *[str(entry.value) for entry in list(VentaApiVersion)],
                ],
                translation_key="api_version",
                mode=selector.SelectSelectorMode.DROPDOWN,
            ),
        ),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            cv.positive_int, vol.Range(min=1)
        ),
    }
)


class ConfigVersion(IntEnum):
    """Config version."""

    V1 = 1
    V2 = 2
    V3 = 3


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Venta."""

    VERSION = ConfigVersion.V3

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            update_interval = timedelta(
                seconds=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            )
            try:
                async with asyncio.timeout(10):
                    api_version = (
                        int(user_input[CONF_API_VERSION])
                        if user_input[CONF_API_VERSION] != AUTO_API_VERSION
                        else None
                    )
                    device = VentaDevice(
                        host,
                        update_interval,
                        api_version,
                        async_get_clientsession(self.hass),
                    )
                    if api_version is None:
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
                    device.host, device.update_interval, device.api_version, device.mac
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def _create_entry(
        self,
        host: str,
        update_interval: timedelta,
        api_version: VentaApiVersion,
        mac: str,
    ) -> FlowResult:
        """Register new entry."""
        if not self.unique_id:
            await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=host,
            data={
                CONF_HOST: host,
                CONF_API_VERSION: api_version,
                CONF_MAC: mac,
                CONF_SCAN_INTERVAL: update_interval.seconds,
            },
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a options flow for Venta."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        data = self.config_entry.data
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={**data, **user_input}
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(cv.positive_int, vol.Range(min=1)),
                }
            ),
        )
