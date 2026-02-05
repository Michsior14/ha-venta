"""Tests for Venta integration __init__ module."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientConnectionError
from homeassistant.const import (
    CONF_API_VERSION,
    CONF_HOST,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
)
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.venta import (
    async_migrate_entry,
    async_setup_entry,
    async_unload_entry,
    async_update_options,
    venta_api_setup,
)
from custom_components.venta.config_flow import ConfigVersion
from custom_components.venta.const import CONF_API_DEFINITION_ID


class TestVentaApiSetup:
    """Tests for venta_api_setup function."""

    async def test_successful_setup(self) -> None:
        """Test successful API setup."""
        hass = MagicMock()

        mock_device = MagicMock()
        mock_device.init = AsyncMock()

        with (
            patch("custom_components.venta.async_get_clientsession"),
            patch("custom_components.venta.VentaDevice", return_value=mock_device),
        ):
            result = await venta_api_setup(
                hass,
                "192.168.1.100",
                timedelta(seconds=10),
                "2/datastructure/datastructure",
            )

            assert result is not None
            mock_device.init.assert_called_once()

    async def test_timeout_error(self) -> None:
        """Test timeout during setup."""
        hass = MagicMock()

        mock_device = MagicMock()
        mock_device.init = AsyncMock(side_effect=asyncio.TimeoutError())

        with (
            patch("custom_components.venta.async_get_clientsession"),
            patch("custom_components.venta.VentaDevice", return_value=mock_device),
            pytest.raises(ConfigEntryNotReady),
        ):
            await venta_api_setup(
                hass,
                "192.168.1.100",
                timedelta(seconds=10),
                "2/datastructure/datastructure",
            )

    async def test_connection_error(self) -> None:
        """Test connection error during setup."""
        hass = MagicMock()

        mock_device = MagicMock()
        mock_device.init = AsyncMock(side_effect=ClientConnectionError())

        with (
            patch("custom_components.venta.async_get_clientsession"),
            patch("custom_components.venta.VentaDevice", return_value=mock_device),
            pytest.raises(ConfigEntryNotReady),
        ):
            await venta_api_setup(
                hass,
                "192.168.1.100",
                timedelta(seconds=10),
                "2/datastructure/datastructure",
            )

    async def test_unexpected_error(self) -> None:
        """Test unexpected error during setup."""
        hass = MagicMock()

        mock_device = MagicMock()
        mock_device.init = AsyncMock(side_effect=ValueError("Unexpected"))

        with (
            patch("custom_components.venta.async_get_clientsession"),
            patch("custom_components.venta.VentaDevice", return_value=mock_device),
        ):
            result = await venta_api_setup(
                hass,
                "192.168.1.100",
                timedelta(seconds=10),
                "2/datastructure/datastructure",
            )

            assert result is None


class TestAsyncSetupEntry:
    """Tests for async_setup_entry function."""

    async def test_successful_setup(self) -> None:
        """Test successful entry setup."""
        hass = MagicMock()
        hass.data = {}
        hass.config_entries.async_forward_entry_setups = AsyncMock()

        entry = MagicMock()
        entry.unique_id = "00:11:22:33:44:55"
        entry.entry_id = "test_entry"
        entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_MAC: "00:11:22:33:44:55",
            CONF_API_DEFINITION_ID: "2/datastructure/datastructure",
            CONF_SCAN_INTERVAL: 10,
        }

        mock_api = MagicMock()
        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        with (
            patch(
                "custom_components.venta.venta_api_setup",
                return_value=mock_api,
            ),
            patch(
                "custom_components.venta.VentaDataUpdateCoordinator",
                return_value=mock_coordinator,
            ),
        ):
            result = await async_setup_entry(hass, entry)

            assert result is True
            assert "venta" in hass.data
            assert entry.entry_id in hass.data["venta"]

    async def test_setup_failure(self) -> None:
        """Test entry setup failure."""
        hass = MagicMock()
        hass.data = {}

        entry = MagicMock()
        entry.unique_id = "00:11:22:33:44:55"
        entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_MAC: "00:11:22:33:44:55",
            CONF_API_DEFINITION_ID: "2/datastructure/datastructure",
        }

        with patch(
            "custom_components.venta.venta_api_setup",
            return_value=None,
        ):
            result = await async_setup_entry(hass, entry)

            assert result is False


class TestAsyncUnloadEntry:
    """Tests for async_unload_entry function."""

    async def test_successful_unload(self) -> None:
        """Test successful entry unload."""
        hass = MagicMock()
        hass.data = {"venta": {"test_entry": MagicMock()}}
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        entry = MagicMock()
        entry.entry_id = "test_entry"

        result = await async_unload_entry(hass, entry)

        assert result is True
        assert "test_entry" not in hass.data["venta"]

    async def test_unload_failure(self) -> None:
        """Test entry unload failure."""
        hass = MagicMock()
        hass.data = {"venta": {"test_entry": MagicMock()}}
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

        entry = MagicMock()
        entry.entry_id = "test_entry"

        result = await async_unload_entry(hass, entry)

        assert result is False
        # Entry should still be present on failure
        assert "test_entry" in hass.data["venta"]


class TestAsyncMigrateEntry:
    """Tests for async_migrate_entry function."""

    async def test_migrate_v1_to_v4(self) -> None:
        """Test migration from V1 to V4."""
        hass = MagicMock()
        entry = MagicMock()
        entry.version = ConfigVersion.V1
        entry.data = {CONF_HOST: "192.168.1.100"}

        # Simulate async_update_entry updating entry.data
        def update_entry_side_effect(
            e: MagicMock, data: dict[str, str] | None = None
        ) -> None:
            if data is not None:
                e.data = data

        hass.config_entries.async_update_entry.side_effect = update_entry_side_effect

        result = await async_migrate_entry(hass, entry)

        assert result is True
        assert entry.version == ConfigVersion.V4

    async def test_migrate_v2_to_v4(self) -> None:
        """Test migration from V2 to V4."""
        hass = MagicMock()
        entry = MagicMock()
        entry.version = ConfigVersion.V2
        entry.data = {CONF_HOST: "192.168.1.100", CONF_API_VERSION: 2}

        result = await async_migrate_entry(hass, entry)

        assert result is True
        assert entry.version == ConfigVersion.V4

    async def test_migrate_v3_to_v4(self) -> None:
        """Test migration from V3 to V4."""
        hass = MagicMock()
        entry = MagicMock()
        entry.version = ConfigVersion.V3
        entry.data = {CONF_HOST: "192.168.1.100", CONF_API_VERSION: 2}

        result = await async_migrate_entry(hass, entry)

        assert result is True
        assert entry.version == ConfigVersion.V4


class TestAsyncUpdateOptions:
    """Tests for async_update_options function."""

    async def test_update_options(self) -> None:
        """Test options update triggers reload."""
        hass = MagicMock()
        hass.config_entries.async_reload = AsyncMock()

        entry = MagicMock()
        entry.entry_id = "test_entry"

        await async_update_options(hass, entry)

        hass.config_entries.async_reload.assert_called_once_with("test_entry")
