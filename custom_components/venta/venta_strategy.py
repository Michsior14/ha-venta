"""Venta API strategies definitions."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from json import JSONDecodeError, dumps
from typing import Any

from aiohttp import ClientSession

from .json import extract_json
from .utils import retry_on_timeout

_LOGGER = logging.getLogger(__name__)


@dataclass
class VentaApiHostDefinition:
    """Venta api host definition."""

    host: str
    port: int


class VentaProtocolStrategy(ABC):
    """Abstract class for Venta API strategy."""

    @abstractmethod
    async def get_status(self, method: str, url: str) -> dict[str, Any] | None:
        """Request status of the Venta device using proper protocol."""

    @abstractmethod
    async def send_action(
        self, method: str, url: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
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

    async def get_status(self, method: str, url: str) -> dict[str, Any] | None:
        """Request status of the Venta device using HTTP protocol."""
        return await self._send_request(method, url)

    async def send_action(
        self, method: str, url: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Send action to the Venta device using HTTP protocol."""
        return await self._send_request(method, url, json)

    @retry_on_timeout()
    async def _send_request(
        self, method: str, url: str, json_action: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Send request to Venta device using HTTP protocol."""

        async def _send() -> dict[str, Any]:
            """Make the http request."""
            _LOGGER.debug("Sending request to %s with data: %s", url, str(json_action))
            async with self._session.request(
                method, f"{self._url}/{url}", json=json_action
            ) as resp:
                json = await resp.json(content_type=None)
                _LOGGER.debug(
                    "Received response from %s: %s",
                    url,
                    str(json),
                )
                return json

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

    _header: VentaTcpHeader | None = None

    def __init__(
        self,
        host_definition: VentaApiHostDefinition,
        buffer_size: int = 2**16,
    ) -> None:
        """Venta TCP strategy constructor."""
        self._host_definition = host_definition
        self._buffer_size = buffer_size

    def set_header(self, header: VentaTcpHeader) -> None:
        """Set the header information."""
        self._header = header

    async def get_status(self, method: str, url: str) -> dict[str, Any] | None:
        """Request status of the Venta device using TCP protocol."""
        message = self._build_message(method, url)
        return await self._send_request(message)

    async def send_action(
        self, method: str, url: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Send action to the Venta device using TCP protocol."""
        message = self._build_message(method, url, json)
        return await self._send_request(message)

    def _build_message(
        self, method: str, url: str, action: dict[str, Any] | None = None
    ) -> str:
        """Build the message to send to the Venta device."""
        header = {
            "Hash": "-42",
            "DeviceName": "HomeAssistant",
        }

        if self._header and self._header.mac and self._header.device_type:
            header.update(
                {
                    "DeviceType": self._header.device_type,
                    "MacAddress": self._header.mac,
                }
            )

        body = dumps(
            {
                "Header": header,
                **(action if action else {}),
            },
            # Venta devices expect no spaces in the JSON string
            separators=(",", ":"),
        )
        return f"{method} /{url}\nContent-Length: {len(body)}\n{body}"

    @retry_on_timeout()
    async def _send_request(self, message: str) -> dict[str, Any] | None:
        """Request data from the Venta device using TCP protocol."""
        writer = None

        try:
            reader, writer = await asyncio.open_connection(
                self._host_definition.host, self._host_definition.port
            )

            try:
                writer.write(message.encode())
                await writer.drain()
            except OSError as err:
                _LOGGER.error(
                    "Unable to send payload %r to %s on port %s: %s",
                    message,
                    self._host_definition.host,
                    self._host_definition.port,
                    err,
                )
                return

            try:
                payload = (await reader.read()).decode().strip()
                _LOGGER.debug(
                    "Receive payload from %s on port %s: %s",
                    self._host_definition.host,
                    self._host_definition.port,
                    payload,
                )

                if not payload:
                    _LOGGER.debug(
                        "Empty response from %s on port %s: %s",
                        self._host_definition.host,
                        self._host_definition.port,
                        payload,
                    )
                    return

                try:
                    return next(extract_json(payload))
                except StopIteration:
                    _LOGGER.error(
                        "Malformed response from %s on port %s: %s",
                        self._host_definition.host,
                        self._host_definition.port,
                        payload,
                    )

            except OSError as err:
                _LOGGER.error(
                    "Unable to receive payload from %s on port %s: %s",
                    self._host_definition.host,
                    self._host_definition.port,
                    err,
                )
            except (JSONDecodeError, TypeError) as err:
                _LOGGER.error(
                    "Unable to parse payload from %s on port %s: %s",
                    self._host_definition.host,
                    self._host_definition.port,
                    err,
                )

        except OSError as err:
            _LOGGER.error(
                "Socket error while connection to %s on port %s: %s",
                self._host_definition.host,
                self._host_definition.port,
                err,
            )
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
