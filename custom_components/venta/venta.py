"""Venta data and api classes."""
import logging
from datetime import timedelta
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any

from aiohttp import ClientConnectionError
from aiohttp import ClientSession, ServerDisconnectedError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, TIMEOUT

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=10)


class VentaApiVersionError(Exception):
    """Can't detect the api version."""


class VentaDeviceType(Enum):
    """Venta device types."""

    UNKNOWN = -1
    LW73_LW74 = 106
    AH550_AH555 = 500


class VentaApiVersion(Enum):
    """Veta api versions."""

    V0 = 0
    V2 = 2
    V3 = 3


API_VERSION_PORTS: dict[VentaApiVersion, int] = {
    VentaApiVersion.V0: 48000,
    VentaApiVersion.V2: 80,
    VentaApiVersion.V3: 80,
}

API_VERSION_ENDPOINTS: dict[VentaApiVersion, str] = {
    VentaApiVersion.V0: "Action",
    VentaApiVersion.V2: "datastructure",
    VentaApiVersion.V3: "api/telemetry?request=set",
}


@dataclass
class VentaData:
    """Class for holding the Venta data."""

    header: dict[str, str | int | bool]
    action: dict[str, str | int | bool]
    info: dict[str, str | int | bool]
    measure: dict[str, str | int | bool]


class VentaDevice:
    """Representation of a Venta device."""

    host: str
    mac: str | None
    device_type: VentaDeviceType
    api_version: VentaApiVersion

    def __init__(
        self, host: str, api_version: int | None, session: ClientSession | None = None
    ) -> None:
        """Venta device constructor."""
        self.host = host
        self.mac = None
        self.device_type = VentaDeviceType.UNKNOWN
        self._session = session
        if api_version is not None:
            self._set_api_version(api_version)

    async def detect_api_version(self) -> None:
        """Detect the api version version."""
        for api_version in reversed(list(VentaApiVersion)):
            self._set_api_version(api_version)
            data = await self._get_data(None, retries=1)
            _LOGGER.debug("Detecting api version: %s", str(data))
            if data is not None and data.get("Header") is not None:
                return
        raise VentaApiVersionError()

    async def init(self) -> None:
        """Initialize the Venta device."""
        data = await self.update()
        self.mac = data.header.get("MacAdress")
        try:
            self.device_type = VentaDeviceType(data.header.get("DeviceType"))
        except ValueError:
            self.device_type = VentaDeviceType.UNKNOWN

    async def update(self, json_action: dict[str, Any] | None = None) -> VentaData:
        """Update the Venta device."""
        data = await self._get_data(json_action)
        return VentaData(
            header=data.get("Header", {}),
            action=data.get("Action", {}),
            info=data.get("Info", {}),
            measure=data.get("Measure", {}),
        )

    def _set_api_version(self, api_version: VentaApiVersion | int) -> None:
        """Set the api version."""
        self.api_version = VentaApiVersion(api_version)
        self._endpoint = f"http://{self.host}:{API_VERSION_PORTS.get(self.api_version)}/{API_VERSION_ENDPOINTS.get(self.api_version)}"

    async def _get_data(
        self, json_action: dict[str, Any] | None = None, retries: int = 3
    ) -> dict[str, Any]:
        """Update resources."""
        try:
            if self._session and not self._session.closed:
                return await self._run_get_data(json_action)
            async with ClientSession() as self._session:
                return await self._run_get_data(json_action)
        except ServerDisconnectedError as error:
            if retries == 0:
                raise error
            return await self._get_data(json_action, retries=retries - 1)

    async def _run_get_data(self, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make the http request."""
        _LOGGER.debug("Sending update request with data: %s", str(json))
        async with self._session.post(self._endpoint, json=json) as resp:
            return await resp.json(content_type="text/plain")


class VentaApi:
    """Keep the Venta instance in one place and centralize the update."""

    device: VentaDevice
    name: str
    host: str
    version: VentaApiVersion

    def __init__(self, device: VentaDevice) -> None:
        """Initialize the Venta Handle."""
        self.device = device
        self.name = "Venta"
        self.host = device.host
        self.version = device.api_version

    async def async_update(self) -> VentaData:
        """Pull the latest data from Venta."""
        return await self.device.update()


class VentaDataUpdateCoordinator(DataUpdateCoordinator[VentaData]):
    """Define an object to hold Venta data."""

    api: VentaApi

    def __init__(self, hass: HomeAssistant, api: VentaApi) -> None:
        """Initialize data coordinator."""
        self.api = api

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)

    async def _async_update_data(self) -> VentaData:
        """Update data via library."""
        async with asyncio.timeout(TIMEOUT):
            try:
                return await self.api.async_update()
            except ClientConnectionError as error:
                _LOGGER.warning("Connection failed for %s", self.api.device.host)
                raise UpdateFailed(error) from error

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        device = self.api.device
        model = device.device_type.name.replace("_", "/")
        return DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, device.mac)},
            manufacturer="Venta",
            name=f"Venta {model}",
            model=model,
            sw_version=self.data.info.get("SWMain"),
        )
