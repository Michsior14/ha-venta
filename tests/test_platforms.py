"""Tests for Venta platform entry point modules."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from custom_components.venta.binary_sensor import (
    async_setup_entry as binary_sensor_setup,
)
from custom_components.venta.humidifier import async_setup_entry as humidifier_setup
from custom_components.venta.light import async_setup_entry as light_setup
from custom_components.venta.select import async_setup_entry as select_setup
from custom_components.venta.sensor import async_setup_entry as sensor_setup
from custom_components.venta.switch import async_setup_entry as switch_setup


class TestPlatformSetupEntry:
    """Tests for platform async_setup_entry functions."""

    async def test_binary_sensor_setup(self) -> None:
        """Test binary sensor platform setup."""
        hass = MagicMock()
        hass.data = {"venta": {"test_entry": MagicMock()}}
        entry = MagicMock()
        entry.entry_id = "test_entry"
        async_add_entities = MagicMock()

        with patch(
            "custom_components.venta.binary_sensor.async_setup_device"
        ) as mock_setup:
            mock_setup.return_value = None
            await binary_sensor_setup(hass, entry, async_add_entities)
            mock_setup.assert_called_once()

    async def test_humidifier_setup(self) -> None:
        """Test humidifier platform setup."""
        hass = MagicMock()
        hass.data = {"venta": {"test_entry": MagicMock()}}
        entry = MagicMock()
        entry.entry_id = "test_entry"
        async_add_entities = MagicMock()

        with patch(
            "custom_components.venta.humidifier.async_setup_device"
        ) as mock_setup:
            mock_setup.return_value = None
            await humidifier_setup(hass, entry, async_add_entities)
            mock_setup.assert_called_once()

    async def test_sensor_setup(self) -> None:
        """Test sensor platform setup."""
        hass = MagicMock()
        hass.data = {"venta": {"test_entry": MagicMock()}}
        entry = MagicMock()
        entry.entry_id = "test_entry"
        async_add_entities = MagicMock()

        with patch("custom_components.venta.sensor.async_setup_device") as mock_setup:
            mock_setup.return_value = None
            await sensor_setup(hass, entry, async_add_entities)
            mock_setup.assert_called_once()

    async def test_switch_setup(self) -> None:
        """Test switch platform setup."""
        hass = MagicMock()
        hass.data = {"venta": {"test_entry": MagicMock()}}
        entry = MagicMock()
        entry.entry_id = "test_entry"
        async_add_entities = MagicMock()

        with patch("custom_components.venta.switch.async_setup_device") as mock_setup:
            mock_setup.return_value = None
            await switch_setup(hass, entry, async_add_entities)
            mock_setup.assert_called_once()

    async def test_light_setup(self) -> None:
        """Test light platform setup."""
        hass = MagicMock()
        hass.data = {"venta": {"test_entry": MagicMock()}}
        entry = MagicMock()
        entry.entry_id = "test_entry"
        async_add_entities = MagicMock()

        with patch("custom_components.venta.light.async_setup_device") as mock_setup:
            mock_setup.return_value = None
            await light_setup(hass, entry, async_add_entities)
            mock_setup.assert_called_once()

    async def test_select_setup(self) -> None:
        """Test select platform setup."""
        hass = MagicMock()
        hass.data = {"venta": {"test_entry": MagicMock()}}
        entry = MagicMock()
        entry.entry_id = "test_entry"
        async_add_entities = MagicMock()

        with patch("custom_components.venta.select.async_setup_device") as mock_setup:
            mock_setup.return_value = None
            await select_setup(hass, entry, async_add_entities)
            mock_setup.assert_called_once()
