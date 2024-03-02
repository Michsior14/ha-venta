"""Venta API strategies definitions."""

import logging
import select
import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass
from json import JSONDecodeError, dumps, loads
from typing import Any
import re

from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)


@dataclass
class VentaApiHostDefinition:
    """Venta api host definition."""

    host: str
    port: int
    timeout: int = 30


class VentaProtocolStrategy(ABC):
    """Abstract class for Venta API strategy."""

    @abstractmethod
    async def get_status(self, method: str, url: str) -> dict[str, Any]:
        """Request status of the Venta device using proper protocol."""

    @abstractmethod
    async def send_action(
        self, method: str, url: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send action to the Venta device using proper protocol."""


class VentaHttpStrategy(VentaProtocolStrategy):
    """Venta HTTP strategy."""

    def __init__(
        self,
        host_definition: VentaApiHostDefinition,
        session: ClientSession | None = None,
    ) -> None:
        """Venta HTTP strategy constructor."""
        self._host_definition = host_definition
        self._url = f"http://{host_definition.host}:{host_definition.port}"
        self._session = session

    async def get_status(self, method: str, url: str) -> dict[str, Any]:
        """Request status of the Venta device using HTTP protocol."""
        return await self._send_request(method, url)

    async def send_action(
        self, method: str, url: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send action to the Venta device using HTTP protocol."""
        return await self._send_request(method, url, json)

    async def _send_request(
        self, method: str, url: str, json_action: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send request to Venta device using HTTP protocol."""

        async def _send() -> dict[str, Any]:
            """Make the http request."""
            _LOGGER.debug("Sending request to %s with data: %s", url, str(json_action))
            async with self._session.request(
                method, f"{self._url}/{url}", json=json_action
            ) as resp:
                return await resp.json(content_type=None)

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
        host_definition: VentaApiHostDefinition,
        header: VentaTcpHeader,
        buffer_size: int = 2**16,
    ) -> None:
        """Venta TCP strategy constructor."""
        self._host_definition = host_definition
        self._header = header
        self._buffer_size = buffer_size

    async def get_status(self, method: str, url: str) -> dict[str, Any]:
        """Request status of the Venta device using TCP protocol."""
        message = self._build_message(method, url)
        return await self._send_request(message)

    async def send_action(
        self, method: str, url: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send action to the Venta device using TCP protocol."""
        message = self._build_message(method, url, json)
        return await self._send_request(message)

    def _build_message(
        self, method: str, url: str, action: dict[str, Any] | None = None
    ) -> str:
        """Build the message to send to the Venta device."""
        body = dumps(
            {
                "Header": {
                    "Hash": "-42",
                    "DeviceName": "HomeAssistant",
                },
                **(action if action else {}),
            }
        )
        # The Venta V0 Humidifier expects a JSON without any whitespaces
        body = body.replace(" ", "")
        return f"{method} /{url}\nContent-Length: {len(body)}\n{body}"

    async def _send_request(self, message: str) -> dict[str, Any]:
        """Request data from the Venta device using TCP protocol."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self._host_definition.timeout)

            # the error here has to be ignored. Seems like the response the socket is getting, is not what it expects or something like that.
            sock.connect((self._host_definition.host, self._host_definition.port))

            try:
                sock.sendall(message.encode())
            except OSError as err:
                _LOGGER.error(
                    "Unable to send payload %r to %s on port %s: %s",
                    message,
                    self._host_definition.host,
                    self._host_definition.port,
                    err,
                )
                return

            readable, _, _ = select.select(
                [sock], [], [], self._host_definition.timeout
            )
            if not readable:
                _LOGGER.warning(
                    (
                        "Timeout (%s second(s)) waiting for a response after "
                        "sending %r to %s on port %s"
                    ),
                    self._host_definition.timeout,
                    message,
                    self._host_definition.host,
                    self._host_definition.port,
                )
                return

            data = sock.recv(self._buffer_size).decode()
            _LOGGER.debug("received Data: %s", data)

            # find the Part of the Response, that is important to us
            json_part = re.search(r'\{.*\}', data)
            if json_part:
                # parse it to a format, Python can handle
                json_string = json_part.group()
                return loads(json_string)
            else:
                _LOGGER.error(
                    "Unable to receive payload from %s on port %s: No JSON Part found",
                    self._host_definition.host,
                    self._host_definition.port,
                )
                return
