"""Shared fixtures for Venta integration tests."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.venta.venta import (
    VentaApi,
    VentaApiDefinition,
    VentaApiEndpointDefinition,
    VentaApiVersion,
    VentaData,
    VentaDevice,
    VentaDeviceType,
)


@pytest.fixture
def mock_venta_data() -> VentaData:
    """Create a mock VentaData object with sample data."""
    return VentaData(
        header={"MacAdress": "00:11:22:33:44:55", "DeviceType": 1},
        action={"Power": True, "TargetHum": 50, "FanSpeed": 3, "TempUnit": 0},
        info={"Warnings": 0, "OperationT": 100, "FilterT": 200},
        measure={"Temperature": 22.5, "Humidity": 45, "Dust": 10, "FanRpm": 1200},
    )


@pytest.fixture
def mock_empty_venta_data() -> VentaData:
    """Create an empty VentaData object."""
    return VentaData(is_empty=True)


@pytest.fixture
def mock_api_definition() -> VentaApiDefinition:
    """Create a mock API definition for V2."""
    return VentaApiDefinition(
        VentaApiVersion.V2,
        VentaApiEndpointDefinition("POST", "datastructure"),
        VentaApiEndpointDefinition("POST", "datastructure"),
    )


@pytest.fixture
def mock_api_definition_v3() -> VentaApiDefinition:
    """Create a mock API definition for V3."""
    return VentaApiDefinition(
        VentaApiVersion.V3,
        VentaApiEndpointDefinition("POST", "api/telemetry"),
        VentaApiEndpointDefinition("POST", "api/telemetry?request=set"),
    )


@pytest.fixture
def mock_api_definition_v0() -> VentaApiDefinition:
    """Create a mock API definition for V0 (TCP)."""
    return VentaApiDefinition(
        VentaApiVersion.V0,
        VentaApiEndpointDefinition("GET", "Complete"),
        VentaApiEndpointDefinition("POST", "Action"),
        48000,
    )


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock aiohttp ClientSession."""
    session = MagicMock()
    session.closed = False

    response = AsyncMock()
    response.json = AsyncMock(
        return_value={
            "Header": {"MacAdress": "00:11:22:33:44:55", "DeviceType": 1},
            "Action": {"Power": True, "TargetHum": 50},
            "Info": {"Warnings": 0},
            "Measure": {"Temperature": 22.5, "Humidity": 45},
        }
    )

    context_manager = AsyncMock()
    context_manager.__aenter__ = AsyncMock(return_value=response)
    context_manager.__aexit__ = AsyncMock(return_value=None)
    session.request = MagicMock(return_value=context_manager)

    return session


@pytest.fixture
def mock_device(
    mock_session: MagicMock, mock_api_definition: VentaApiDefinition
) -> VentaDevice:
    """Create a mock VentaDevice."""

    device = VentaDevice(
        host="192.168.1.100",
        update_interval=timedelta(seconds=10),
        api_definition_id=mock_api_definition.id,
        session=mock_session,
    )
    device.mac = "00:11:22:33:44:55"
    device.device_type = VentaDeviceType.LP60
    return device


@pytest.fixture
def mock_coordinator(mock_device: VentaDevice, mock_venta_data: VentaData) -> MagicMock:
    """Create a mock VentaDataUpdateCoordinator."""
    coordinator = MagicMock()
    coordinator.api = VentaApi(mock_device)
    coordinator.data = mock_venta_data
    coordinator.device_info = {
        "identifiers": {("venta", "00:11:22:33:44:55")},
        "name": "Venta",
        "manufacturer": "Venta",
        "model": "LP60",
    }
    return coordinator
