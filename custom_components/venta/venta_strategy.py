"""Venta API strategies definitions."""

import logging
import select
import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from json import loads, dumps

from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)


@dataclass
class VentaApiHostDefinition:
    """Venta api endpoint definition."""

    host: str
    port: int = 80
    timeout: int = 30


class VentaProtocolStrategy(ABC):
    """Abstract class for Venta API strategy."""

    @abstractmethod
    async def get_status(self, endpoint: str) -> dict[str, Any]:
        """Request status of the Venta device using proper protocol."""

    @abstractmethod
    async def send_action(
        self, endpoint: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send action to the Venta device using proper protocol."""


class VentaHttpStrategy(VentaProtocolStrategy):
    """Venta HTTP strategy."""

    def __init__(
        self, host: VentaApiHostDefinition, session: ClientSession | None = None
    ) -> None:
        """Venta HTTP strategy constructor."""
        self._host = host
        self._url = f"http://{host.host}:{host.port}"
        self._session = session

    async def get_status(self, endpoint: str) -> dict[str, Any]:
        """Request status of the Venta device using HTTP protocol."""
        return await self._send_request(endpoint)

    async def send_action(
        self, endpoint: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send action to the Venta device using HTTP protocol."""
        return await self._send_request(endpoint, json)

    async def _send_request(
        self, endpoint: str, json_action: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send request to Venta device using HTTP protocol."""

        async def _send() -> dict[str, Any]:
            """Make the http request."""
            _LOGGER.debug(
                "Sending request to %s with data: %s", endpoint, str(json_action)
            )
            async with self._session.post(
                f"{self._url}/{endpoint}", json=json_action
            ) as resp:
                return await resp.json(content_type="text/plain")

        if self._session and not self._session.closed:
            return await _send()
        async with ClientSession() as self._session:
            return await _send()


@dataclass
class VentaTcpHeader:
    """Venta TCP header."""

    mac: str
    device_type: int


class VentaTcpStrategy(VentaProtocolStrategy):
    """Venta raw TCP strategy."""

    def __init__(
        self,
        host: VentaApiHostDefinition,
        header: VentaTcpHeader,
        buffer_size: int = 2**16,
    ) -> None:
        """Venta TCP strategy constructor."""
        self._host = host
        self._header = header
        self._buffer_size = buffer_size

    async def get_status(self, endpoint: str) -> dict[str, Any]:
        """Request status of the Venta device using TCP protocol."""
        message = self._build_message("GET", endpoint)
        return await self._send_request(message)

    async def send_action(
        self, endpoint: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send action to the Venta device using TCP protocol."""
        message = self._build_message("POST", endpoint, json)
        return await self._send_request(message)

    def _build_message(
        self, method: str, endpoint: str, action: dict[str, Any] | None = None
    ) -> str:
        """Build the message to send to the Venta device."""
        body = dumps(
            {
                "Header": {
                    "DeviceType": self._header.device_type,
                    "MacAdress": self._header.mac,
                    "Hash": "-42",
                    "DeviceName": "HomeAssistant",
                },
                **(action if action else {}),
            }
        )
        return f"{method} /{endpoint}\nContent-Length: {len(body)}\n\n{body}\n\n"

    async def _send_request(self, message: str) -> dict[str, Any]:
        """Request data from the Venta device using TCP protocol."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self._host.timeout)
            try:
                sock.connect((self._host.host, self._host.port))
            except OSError as err:
                _LOGGER.error(
                    "Unable to connect to %s on port %s: %s",
                    self._host.host,
                    self._host.port,
                    err,
                )
                return

            try:
                sock.sendall(message.encode())
            except OSError as err:
                _LOGGER.error(
                    "Unable to send payload %r to %s on port %s: %s",
                    message,
                    self._host.host,
                    self._host.port,
                    err,
                )
                return

            readable, _, _ = select.select([sock], [], [], self._host.timeout)
            if not readable:
                _LOGGER.warning(
                    (
                        "Timeout (%s second(s)) waiting for a response after "
                        "sending %r to %s on port %s"
                    ),
                    self._host.timeout,
                    message,
                    self._host.host,
                    self._host.port,
                )
                return

            return loads(sock.recv(self._buffer_size).decode())
