"""Tests for the Venta core module."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.venta.venta import (
    API_DEFINITIONS,
    VentaApi,
    VentaApiDefinition,
    VentaApiEndpointDefinition,
    VentaApiVersion,
    VentaData,
    VentaDevice,
    VentaDeviceType,
)


class TestVentaData:
    """Tests for VentaData dataclass."""

    def test_default_values(self) -> None:
        """Test default values are empty dicts."""
        data = VentaData()
        assert data.header == {}
        assert data.action == {}
        assert data.info == {}
        assert data.measure == {}
        assert data.is_empty is False

    def test_with_values(self) -> None:
        """Test initialization with values."""
        data = VentaData(
            header={"MacAdress": "00:11:22:33:44:55"},
            action={"Power": True},
            info={"Warnings": 0},
            measure={"Temperature": 22.5},
        )
        assert data.header["MacAdress"] == "00:11:22:33:44:55"
        assert data.action["Power"] is True
        assert data.info["Warnings"] == 0
        assert data.measure["Temperature"] == 22.5

    def test_is_empty_flag(self) -> None:
        """Test the is_empty flag."""
        empty_data = VentaData(is_empty=True)
        assert empty_data.is_empty is True


class TestVentaApiEndpointDefinition:
    """Tests for VentaApiEndpointDefinition dataclass."""

    def test_creation(self) -> None:
        """Test endpoint definition creation."""
        endpoint = VentaApiEndpointDefinition("POST", "api/telemetry")
        assert endpoint.method == "POST"
        assert endpoint.url == "api/telemetry"


class TestVentaApiDefinition:
    """Tests for VentaApiDefinition dataclass."""

    def test_creation_with_defaults(self) -> None:
        """Test API definition with default port."""
        definition = VentaApiDefinition(
            VentaApiVersion.V2,
            VentaApiEndpointDefinition("POST", "datastructure"),
            VentaApiEndpointDefinition("POST", "datastructure"),
        )
        assert definition.version == VentaApiVersion.V2
        assert definition.port == 80

    def test_creation_with_custom_port(self) -> None:
        """Test API definition with custom port."""
        definition = VentaApiDefinition(
            VentaApiVersion.V0,
            VentaApiEndpointDefinition("GET", "Complete"),
            VentaApiEndpointDefinition("POST", "Action"),
            48000,
        )
        assert definition.port == 48000

    def test_id_property(self) -> None:
        """Test ID generation property."""
        definition = VentaApiDefinition(
            VentaApiVersion.V2,
            VentaApiEndpointDefinition("POST", "datastructure"),
            VentaApiEndpointDefinition("POST", "datastructure"),
        )
        # ID format is version/status_url/action_url
        assert definition.id == "2/datastructure/datastructure"

    def test_id_property_v0(self) -> None:
        """Test ID generation for V0 with custom port."""
        definition = VentaApiDefinition(
            VentaApiVersion.V0,
            VentaApiEndpointDefinition("GET", "Complete"),
            VentaApiEndpointDefinition("POST", "Action"),
            48000,
        )
        # ID format is version/status_url/action_url
        assert definition.id == "0/Complete/Action"


class TestApiDefinitions:
    """Tests for the global API_DEFINITIONS list."""

    def test_definitions_exist(self) -> None:
        """Test that API definitions are defined."""
        assert len(API_DEFINITIONS) >= 3

    def test_v3_definition(self) -> None:
        """Test V3 API definition."""
        v3_defs = [d for d in API_DEFINITIONS if d.version == VentaApiVersion.V3]
        # There are 2 V3 definitions: one for telemetry and one for sensordata.json
        assert len(v3_defs) >= 1
        telemetry_def = [d for d in v3_defs if "telemetry" in d.status.url]
        assert len(telemetry_def) == 1
        assert telemetry_def[0].port == 80

    def test_v2_definition(self) -> None:
        """Test V2 API definition."""
        v2_defs = [d for d in API_DEFINITIONS if d.version == VentaApiVersion.V2]
        assert len(v2_defs) == 1
        assert v2_defs[0].status.url == "datastructure"

    def test_v0_definition(self) -> None:
        """Test V0 (TCP) API definition."""
        v0_defs = [d for d in API_DEFINITIONS if d.version == VentaApiVersion.V0]
        assert len(v0_defs) == 1
        assert v0_defs[0].port == 48000

    def test_unique_ids(self) -> None:
        """Test that all definitions have unique IDs."""
        ids = [d.id for d in API_DEFINITIONS]
        assert len(ids) == len(set(ids))


class TestVentaDeviceType:
    """Tests for VentaDeviceType enum."""

    def test_device_types_exist(self) -> None:
        """Test that device types are defined."""
        assert VentaDeviceType.LP60.value == 1
        assert VentaDeviceType.LPH60.value == 2
        assert VentaDeviceType.UNKNOWN.value == -1

    def test_all_types_have_values(self) -> None:
        """Test all device types have integer values."""
        for device_type in VentaDeviceType:
            assert isinstance(device_type.value, int)


class TestVentaApiVersion:
    """Tests for VentaApiVersion enum."""

    def test_versions_exist(self) -> None:
        """Test that API versions are defined."""
        assert VentaApiVersion.V0.value == 0
        assert VentaApiVersion.V2.value == 2
        assert VentaApiVersion.V3.value == 3


class TestVentaDevice:
    """Tests for VentaDevice class."""

    def test_initialization(self) -> None:
        """Test device initialization."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="2/datastructure/datastructure",
            session=None,
        )
        assert device.host == "192.168.1.100"
        assert device.update_interval == timedelta(seconds=10)
        assert device.mac is None
        assert device.device_type == VentaDeviceType.UNKNOWN

    def test_initialization_with_invalid_api_id(self) -> None:
        """Test device initialization with None api_definition_id."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id=None,
            session=None,
        )
        assert device.host == "192.168.1.100"

    async def test_map_data_with_valid_data(self) -> None:
        """Test _map_data with valid response."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="2/datastructure/datastructure",
            session=None,
        )
        data = {
            "Header": {"MacAdress": "00:11:22:33:44:55", "DeviceType": 1},
            "Action": {"Power": True, "FanSpeed": 3},
            "Info": {"Warnings": 0},
            "Measure": {"Temperature": 22.5},
        }
        venta_data = await device._map_data(data)
        assert venta_data.header["MacAdress"] == "00:11:22:33:44:55"
        assert venta_data.action["Power"] is True
        assert venta_data.info["Warnings"] == 0
        assert venta_data.measure["Temperature"] == 22.5

    async def test_map_data_with_none(self) -> None:
        """Test _map_data with None returns empty VentaData."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="2/datastructure/datastructure",
            session=None,
        )
        venta_data = await device._map_data(None)
        assert venta_data.is_empty is True

    def test_set_api_definition(self) -> None:
        """Test _set_api_definition sets correct values."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="2/datastructure/datastructure",
            session=None,
        )
        assert device.api_version == VentaApiVersion.V2
        assert device.api_definition.version == VentaApiVersion.V2


class TestVentaApi:
    """Tests for VentaApi class."""

    def test_initialization(self) -> None:
        """Test API wrapper initialization."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="2/datastructure/datastructure",
            session=None,
        )
        api = VentaApi(device)
        assert api.device == device
        assert api.name == "Venta"

    async def test_async_update(self) -> None:
        """Test async_update calls device status."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="2/datastructure/datastructure",
            session=None,
        )
        device.status = AsyncMock(
            return_value=VentaData(
                header={"MacAdress": "00:11:22:33:44:55"},
                action={"Power": True},
            )
        )
        api = VentaApi(device)
        result = await api.async_update()
        assert result.header["MacAdress"] == "00:11:22:33:44:55"
        device.status.assert_called_once()


class TestVentaDeviceInit:
    """Tests for VentaDevice.init method."""

    async def test_init_sets_mac(self) -> None:
        """Test init sets MAC address."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="2/datastructure/datastructure",
            session=None,
        )

        mock_strategy = MagicMock()
        mock_strategy.get_status = AsyncMock(
            return_value={"Header": {"MacAdress": "00:11:22:33:44:55", "DeviceType": 1}}
        )
        device._strategy = mock_strategy

        await device.init()

        assert device.mac == "00:11:22:33:44:55"
        assert device.device_type == VentaDeviceType.LP60

    async def test_init_with_device_id(self) -> None:
        """Test init with DeviceId instead of MacAdress."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="2/datastructure/datastructure",
            session=None,
        )

        mock_strategy = MagicMock()
        mock_strategy.get_status = AsyncMock(
            return_value={"Header": {"DeviceId": "device123", "DeviceType": 2}}
        )
        device._strategy = mock_strategy

        await device.init()

        assert device.mac == "device123"
        assert device.device_type == VentaDeviceType.LPH60

    async def test_init_unknown_device_type(self) -> None:
        """Test init with unknown device type."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="2/datastructure/datastructure",
            session=None,
        )

        mock_strategy = MagicMock()
        mock_strategy.get_status = AsyncMock(
            return_value={
                "Header": {"MacAdress": "00:11:22:33:44:55", "DeviceType": 999}
            }
        )
        device._strategy = mock_strategy

        await device.init()

        assert device.device_type == VentaDeviceType.UNKNOWN


class TestVentaDeviceAction:
    """Tests for VentaDevice.action method."""

    async def test_action_success(self) -> None:
        """Test successful action."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="2/datastructure/datastructure",
            session=None,
        )

        mock_strategy = MagicMock()
        mock_strategy.send_action = AsyncMock(
            return_value={"Header": {"MacAdress": "00:11:22:33:44:55"}}
        )
        device._strategy = mock_strategy

        mock_coordinator = MagicMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        result = await device.action({"Power": True}, mock_coordinator)

        assert result.header["MacAdress"] == "00:11:22:33:44:55"
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_action_not_supported(self) -> None:
        """Test action on device without action support."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="3/sensordata.json/None",  # V3 without action
            session=None,
        )

        mock_coordinator = MagicMock()

        with pytest.raises(ValueError, match="Action is not supported"):
            await device.action({"Power": True}, mock_coordinator)


class TestVentaDeviceStatus:
    """Tests for VentaDevice.status method."""

    async def test_status_returns_data(self) -> None:
        """Test status returns VentaData."""
        device = VentaDevice(
            host="192.168.1.100",
            update_interval=timedelta(seconds=10),
            api_definition_id="2/datastructure/datastructure",
            session=None,
        )

        mock_strategy = MagicMock()
        mock_strategy.get_status = AsyncMock(
            return_value={
                "Header": {"MacAdress": "00:11:22:33:44:55"},
                "Action": {"Power": True},
            }
        )
        device._strategy = mock_strategy

        result = await device.status()

        assert result.header["MacAdress"] == "00:11:22:33:44:55"
        assert result.action["Power"] is True
