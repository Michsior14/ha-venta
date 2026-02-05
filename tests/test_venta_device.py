"""Tests for venta_device module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.venta.venta_device import async_setup_device


class TestAsyncSetupDevice:
    """Tests for async_setup_device function."""

    async def test_successful_setup(self) -> None:
        """Test successful device setup."""
        coordinator = MagicMock()
        coordinator.api.device.device_type.value = 1
        async_add_entities = MagicMock()
        hass = MagicMock()

        mock_module = MagicMock()
        mock_module.async_setup_binary_sensor = AsyncMock()

        with patch(
            "custom_components.venta.venta_device.async_import_module",
            return_value=mock_module,
        ):
            await async_setup_device(
                "binary_sensor", hass, coordinator, async_add_entities
            )
            mock_module.async_setup_binary_sensor.assert_called_once_with(
                coordinator, async_add_entities
            )

    async def test_function_not_found(self) -> None:
        """Test when setup function is not found in module."""
        coordinator = MagicMock()
        coordinator.api.device.device_type.value = 1
        async_add_entities = MagicMock()
        hass = MagicMock()

        mock_module = MagicMock(spec=[])  # No methods

        with patch(
            "custom_components.venta.venta_device.async_import_module",
            return_value=mock_module,
        ):
            # Should not raise, just log debug
            await async_setup_device(
                "binary_sensor", hass, coordinator, async_add_entities
            )

    async def test_import_error(self) -> None:
        """Test handling of import error."""
        coordinator = MagicMock()
        coordinator.api.device.device_type.value = 999
        async_add_entities = MagicMock()
        hass = MagicMock()

        with patch(
            "custom_components.venta.venta_device.async_import_module",
            side_effect=ImportError("Module not found"),
        ):
            # Should not raise, just log error
            await async_setup_device("sensor", hass, coordinator, async_add_entities)

    async def test_all_entity_types(self) -> None:
        """Test setup for all entity types."""
        entity_types = [
            "binary_sensor",
            "humidifier",
            "sensor",
            "switch",
            "light",
            "select",
        ]

        for entity_type in entity_types:
            coordinator = MagicMock()
            coordinator.api.device.device_type.value = 1
            async_add_entities = MagicMock()
            hass = MagicMock()

            mock_module = MagicMock()
            setattr(mock_module, f"async_setup_{entity_type}", AsyncMock())

            with patch(
                "custom_components.venta.venta_device.async_import_module",
                return_value=mock_module,
            ):
                await async_setup_device(
                    entity_type, hass, coordinator, async_add_entities
                )
                getattr(
                    mock_module, f"async_setup_{entity_type}"
                ).assert_called_once_with(coordinator, async_add_entities)
