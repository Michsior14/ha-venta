"""Tests for the Venta config flow module."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientError
from homeassistant.const import (
    CONF_API_VERSION,
    CONF_HOST,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
)
from homeassistant.data_entry_flow import FlowResultType

from custom_components.venta.config_flow import (
    ConfigFlow,
    ConfigVersion,
)
from custom_components.venta.const import (
    AUTO_API_VERSION,
    CONF_API_DEFINITION_ID,
    DEFAULT_SCAN_INTERVAL,
)
from custom_components.venta.venta import (
    VentaApiDefinition,
    VentaApiEndpointDefinition,
    VentaApiVersion,
    VentaApiVersionError,
)


class TestConfigVersion:
    """Tests for ConfigVersion enum."""

    def test_versions_exist(self) -> None:
        """Test that config versions are defined."""
        assert ConfigVersion.V1 == 1
        assert ConfigVersion.V2 == 2
        assert ConfigVersion.V3 == 3
        assert ConfigVersion.V4 == 4

    def test_max_version(self) -> None:
        """Test that max version is V4."""
        assert max(ConfigVersion) == ConfigVersion.V4


class TestConfigFlow:
    """Tests for ConfigFlow class."""

    def test_version(self) -> None:
        """Test config flow version is max ConfigVersion."""
        assert ConfigFlow.VERSION == max(ConfigVersion)

    async def test_async_step_user_shows_form(self) -> None:
        """Test that user step shows form initially."""
        flow = ConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_user()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    async def test_async_step_user_connection_timeout(self) -> None:
        """Test handling of connection timeout."""
        flow = ConfigFlow()
        flow.hass = MagicMock()

        with (
            patch("custom_components.venta.config_flow.async_get_clientsession"),
            patch(
                "custom_components.venta.config_flow.VentaDevice"
            ) as mock_device_class,
        ):
            mock_device = MagicMock()
            mock_device.detect_api = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_device_class.return_value = mock_device

            result = await flow.async_step_user(
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_API_VERSION: AUTO_API_VERSION,
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"]["base"] == "cannot_connect"

    async def test_async_step_user_client_error(self) -> None:
        """Test handling of client error."""
        flow = ConfigFlow()
        flow.hass = MagicMock()

        with (
            patch("custom_components.venta.config_flow.async_get_clientsession"),
            patch(
                "custom_components.venta.config_flow.VentaDevice"
            ) as mock_device_class,
        ):
            mock_device = MagicMock()
            mock_device.detect_api = AsyncMock(side_effect=ClientError())
            mock_device_class.return_value = mock_device

            result = await flow.async_step_user(
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_API_VERSION: AUTO_API_VERSION,
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"]["base"] == "cannot_connect"

    async def test_async_step_user_api_version_error(self) -> None:
        """Test handling of API version detection error."""
        flow = ConfigFlow()
        flow.hass = MagicMock()

        with (
            patch("custom_components.venta.config_flow.async_get_clientsession"),
            patch(
                "custom_components.venta.config_flow.VentaDevice"
            ) as mock_device_class,
        ):
            mock_device = MagicMock()
            mock_device.detect_api = AsyncMock(side_effect=VentaApiVersionError())
            mock_device_class.return_value = mock_device

            result = await flow.async_step_user(
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_API_VERSION: AUTO_API_VERSION,
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"]["base"] == "cannot_detect_api_version"

    async def test_async_step_user_unknown_error(self) -> None:
        """Test handling of unknown errors."""
        flow = ConfigFlow()
        flow.hass = MagicMock()

        with (
            patch("custom_components.venta.config_flow.async_get_clientsession"),
            patch(
                "custom_components.venta.config_flow.VentaDevice"
            ) as mock_device_class,
        ):
            mock_device = MagicMock()
            mock_device.detect_api = AsyncMock(side_effect=ValueError("Unknown"))
            mock_device_class.return_value = mock_device

            result = await flow.async_step_user(
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_API_VERSION: AUTO_API_VERSION,
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["errors"]["base"] == "unknown"

    async def test_async_step_user_success(self) -> None:
        """Test successful device configuration."""
        flow = ConfigFlow()
        flow.hass = MagicMock()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        mock_api_definition = VentaApiDefinition(
            VentaApiVersion.V2,
            VentaApiEndpointDefinition("POST", "datastructure"),
            VentaApiEndpointDefinition("POST", "datastructure"),
        )

        with (
            patch("custom_components.venta.config_flow.async_get_clientsession"),
            patch(
                "custom_components.venta.config_flow.VentaDevice"
            ) as mock_device_class,
        ):
            mock_device = MagicMock()
            mock_device.host = "192.168.1.100"
            mock_device.update_interval = timedelta(seconds=10)
            mock_device.api_definition = mock_api_definition
            mock_device.mac = "00:11:22:33:44:55"
            mock_device.detect_api = AsyncMock()
            mock_device.init = AsyncMock()
            mock_device_class.return_value = mock_device

            result = await flow.async_step_user(
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_API_VERSION: AUTO_API_VERSION,
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                }
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["title"] == "192.168.1.100"
            assert result["data"][CONF_HOST] == "192.168.1.100"
            assert result["data"][CONF_MAC] == "00:11:22:33:44:55"
            assert result["data"][CONF_API_DEFINITION_ID] == mock_api_definition.id

    async def test_async_step_user_with_explicit_api_version(self) -> None:
        """Test configuration with explicit API version."""
        flow = ConfigFlow()
        flow.hass = MagicMock()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        mock_api_definition = VentaApiDefinition(
            VentaApiVersion.V3,
            VentaApiEndpointDefinition("POST", "api/telemetry"),
            VentaApiEndpointDefinition("POST", "api/telemetry?request=set"),
        )

        with (
            patch("custom_components.venta.config_flow.async_get_clientsession"),
            patch(
                "custom_components.venta.config_flow.VentaDevice"
            ) as mock_device_class,
        ):
            mock_device = MagicMock()
            mock_device.host = "192.168.1.100"
            mock_device.update_interval = timedelta(seconds=10)
            mock_device.api_definition = mock_api_definition
            mock_device.mac = "00:11:22:33:44:55"
            mock_device.detect_api = AsyncMock()
            mock_device.init = AsyncMock()
            mock_device_class.return_value = mock_device

            result = await flow.async_step_user(
                {
                    CONF_HOST: "192.168.1.100",
                    CONF_API_VERSION: "3",  # Explicit V3
                    CONF_SCAN_INTERVAL: 30,
                }
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            mock_device.detect_api.assert_called_once_with(api_version=3)


# Note: OptionsFlowHandler tests are skipped because newer Home Assistant
# versions use a property for config_entry that doesn't allow direct assignment.
# The options flow is tested through integration tests instead.
