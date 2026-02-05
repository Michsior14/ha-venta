"""Tests for the Venta strategy module."""

from __future__ import annotations

from json import dumps
from unittest.mock import AsyncMock, MagicMock, patch


from custom_components.venta.venta_strategy import (
    VentaApiHostDefinition,
    VentaHttpStrategy,
    VentaTcpHeader,
    VentaTcpStrategy,
)


class TestVentaApiHostDefinition:
    """Tests for VentaApiHostDefinition dataclass."""

    def test_creation(self) -> None:
        """Test host definition creation."""
        host_def = VentaApiHostDefinition("192.168.1.100", 80)
        assert host_def.host == "192.168.1.100"
        assert host_def.port == 80  # noqa: PLR2004

    def test_custom_port(self) -> None:
        """Test host definition with custom port."""
        host_def = VentaApiHostDefinition("192.168.1.100", 48000)
        assert host_def.port == 48000  # noqa: PLR2004


class TestVentaTcpHeader:
    """Tests for VentaTcpHeader dataclass."""

    def test_creation(self) -> None:
        """Test TCP header creation."""
        header = VentaTcpHeader("00:11:22:33:44:55", 1)
        assert header.mac == "00:11:22:33:44:55"
        assert header.device_type == 1


class TestVentaHttpStrategy:
    """Tests for VentaHttpStrategy class."""

    def test_initialization(self) -> None:
        """Test HTTP strategy initialization."""
        host_def = VentaApiHostDefinition("192.168.1.100", 80)
        strategy = VentaHttpStrategy(host_def)
        assert strategy._url == "http://192.168.1.100:80"

    def test_initialization_with_session(self) -> None:
        """Test HTTP strategy initialization with session."""
        host_def = VentaApiHostDefinition("192.168.1.100", 80)
        mock_session = MagicMock()
        strategy = VentaHttpStrategy(host_def, mock_session)
        assert strategy._session == mock_session

    async def test_get_status(self) -> None:
        """Test get_status makes correct request."""
        host_def = VentaApiHostDefinition("192.168.1.100", 80)
        mock_session = MagicMock()
        mock_session.closed = False

        response_data = {"Header": {"MacAdress": "00:11:22:33:44:55"}}
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=response_data)

        context_manager = AsyncMock()
        context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_session.request = MagicMock(return_value=context_manager)

        strategy = VentaHttpStrategy(host_def, mock_session)
        result = await strategy.get_status("POST", "datastructure")

        assert result == response_data
        mock_session.request.assert_called_once_with(
            "POST", "http://192.168.1.100:80/datastructure", json=None
        )

    async def test_send_action(self) -> None:
        """Test send_action with JSON payload."""
        host_def = VentaApiHostDefinition("192.168.1.100", 80)
        mock_session = MagicMock()
        mock_session.closed = False

        response_data = {"Status": "OK"}
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=response_data)

        context_manager = AsyncMock()
        context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_session.request = MagicMock(return_value=context_manager)

        strategy = VentaHttpStrategy(host_def, mock_session)
        action = {"Action": {"Power": True}}
        result = await strategy.send_action("POST", "datastructure", action)

        assert result == response_data
        mock_session.request.assert_called_once_with(
            "POST", "http://192.168.1.100:80/datastructure", json=action
        )


class TestVentaTcpStrategy:
    """Tests for VentaTcpStrategy class."""

    def test_initialization(self) -> None:
        """Test TCP strategy initialization."""
        host_def = VentaApiHostDefinition("192.168.1.100", 48000)
        strategy = VentaTcpStrategy(host_def)
        assert strategy._host_definition == host_def
        assert strategy._buffer_size == 2**16
        assert strategy._header is None

    def test_initialization_custom_buffer(self) -> None:
        """Test TCP strategy with custom buffer size."""
        host_def = VentaApiHostDefinition("192.168.1.100", 48000)
        strategy = VentaTcpStrategy(host_def, buffer_size=1024)
        assert strategy._buffer_size == 1024  # noqa: PLR2004

    def test_set_header(self) -> None:
        """Test setting TCP header."""
        host_def = VentaApiHostDefinition("192.168.1.100", 48000)
        strategy = VentaTcpStrategy(host_def)
        header = VentaTcpHeader("00:11:22:33:44:55", 1)
        strategy.set_header(header)
        assert strategy._header == header

    def test_build_message_without_header(self) -> None:
        """Test message building without header info."""
        host_def = VentaApiHostDefinition("192.168.1.100", 48000)
        strategy = VentaTcpStrategy(host_def)
        message = strategy._build_message("GET", "Complete")

        assert "GET /Complete" in message
        assert "Content-Length:" in message
        assert '"Hash":"-42"' in message
        assert '"DeviceName":"HomeAssistant"' in message

    def test_build_message_with_header(self) -> None:
        """Test message building with header info."""
        host_def = VentaApiHostDefinition("192.168.1.100", 48000)
        strategy = VentaTcpStrategy(host_def)
        header = VentaTcpHeader("00:11:22:33:44:55", 1)
        strategy.set_header(header)
        message = strategy._build_message("GET", "Complete")

        assert '"MacAddress":"00:11:22:33:44:55"' in message
        assert '"DeviceType":1' in message

    def test_build_message_with_action(self) -> None:
        """Test message building with action payload."""
        host_def = VentaApiHostDefinition("192.168.1.100", 48000)
        strategy = VentaTcpStrategy(host_def)
        action = {"Action": {"Power": True, "FanSpeed": 3}}
        message = strategy._build_message("POST", "Action", action)

        assert "POST /Action" in message
        assert '"Action"' in message
        assert '"Power":true' in message
        assert '"FanSpeed":3' in message

    async def test_get_status_success(self) -> None:
        """Test get_status with successful response."""
        host_def = VentaApiHostDefinition("192.168.1.100", 48000)
        strategy = VentaTcpStrategy(host_def)

        response_data = {"Header": {"MacAdress": "00:11:22:33:44:55"}, "Action": {}}

        with patch("asyncio.open_connection") as mock_open_connection:
            mock_reader = AsyncMock()
            mock_reader.read = AsyncMock(return_value=dumps(response_data).encode())
            mock_writer = AsyncMock()
            mock_writer.write = MagicMock()
            mock_writer.drain = AsyncMock()
            mock_writer.close = MagicMock()
            mock_writer.wait_closed = AsyncMock()
            mock_open_connection.return_value = (mock_reader, mock_writer)

            result = await strategy.get_status("GET", "Complete")

            assert result == response_data

    async def test_send_action_success(self) -> None:
        """Test send_action with successful response."""
        host_def = VentaApiHostDefinition("192.168.1.100", 48000)
        strategy = VentaTcpStrategy(host_def)

        response_data = {"Status": "OK"}
        action = {"Action": {"Power": True}}

        with patch("asyncio.open_connection") as mock_open_connection:
            mock_reader = AsyncMock()
            mock_reader.read = AsyncMock(return_value=dumps(response_data).encode())
            mock_writer = AsyncMock()
            mock_writer.write = MagicMock()
            mock_writer.drain = AsyncMock()
            mock_writer.close = MagicMock()
            mock_writer.wait_closed = AsyncMock()
            mock_open_connection.return_value = (mock_reader, mock_writer)

            result = await strategy.send_action("POST", "Action", action)

            assert result == response_data

    async def test_empty_response(self) -> None:
        """Test handling of empty response."""
        host_def = VentaApiHostDefinition("192.168.1.100", 48000)
        strategy = VentaTcpStrategy(host_def)

        with patch("asyncio.open_connection") as mock_open_connection:
            mock_reader = AsyncMock()
            mock_reader.read = AsyncMock(return_value=b"")
            mock_writer = AsyncMock()
            mock_writer.write = MagicMock()
            mock_writer.drain = AsyncMock()
            mock_writer.close = MagicMock()
            mock_writer.wait_closed = AsyncMock()
            mock_open_connection.return_value = (mock_reader, mock_writer)

            result = await strategy.get_status("GET", "Complete")

            assert result is None

    async def test_connection_error(self) -> None:
        """Test handling of connection errors."""
        host_def = VentaApiHostDefinition("192.168.1.100", 48000)
        strategy = VentaTcpStrategy(host_def)

        with patch("asyncio.open_connection") as mock_open_connection:
            mock_open_connection.side_effect = OSError("Connection refused")

            result = await strategy.get_status("GET", "Complete")

            assert result is None
