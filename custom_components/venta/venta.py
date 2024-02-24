"""Venta data and api classes."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from aiohttp import ClientConnectionError, ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .venta_strategy import (
    VentaApiHostDefinition,
    VentaHttpStrategy,
    VentaTcpHeader,
    VentaTcpStrategy,
)

_LOGGER = logging.getLogger(__name__)


class VentaApiVersionError(Exception):
    """Can't detect the api version."""


class VentaDeviceType(Enum):
    """Venta device types."""

    UNKNOWN = -1
    LW60 = 2
    AH902 = 12
    LW73_LW74 = 106
    AS150 = 150
    AH550_AH555 = 500


class VentaApiVersion(Enum):
    """Veta api versions."""

    V0 = 0
    V2 = 2
    V3 = 3


@dataclass
class VentaApiEndpointDefinition:
    """Venta api endpoint definition."""

    status: str
    action: str
    port: int = 80


API_VERSION_ENDPOINTS: dict[VentaApiVersion, VentaApiEndpointDefinition] = {
    VentaApiVersion.V0: VentaApiEndpointDefinition("Complete", "Action", 48000),
    VentaApiVersion.V2: VentaApiEndpointDefinition("datastructure", "datastructure"),
    VentaApiVersion.V3: VentaApiEndpointDefinition(
        "api/telemetry", "api/telemetry?request=set"
    ),
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
    update_interval: timedelta
    endpoint_definition: VentaApiEndpointDefinition

    def __init__(
        self,
        host: str,
        update_interval: timedelta,
        api_version: int | None,
        session: ClientSession | None = None,
    ) -> None:
        """Venta device constructor."""
        self.host = host
        self.update_interval = update_interval
        self.mac = None
        self.device_type = VentaDeviceType.UNKNOWN
        self._session = session
        if api_version is not None:
            self._set_api_defaults(api_version)

    async def detect_api_version(self) -> None:
        """Detect the api version version."""
        for api_version in reversed(list(VentaApiVersion)):
            self._set_api_defaults(api_version)
            data = await self._strategy.get_status(self.endpoint_definition.status)
            _LOGGER.debug("Detecting api version: %s", str(data))
            if data is not None and data.get("Header") is not None:
                return
            await asyncio.sleep(5.0)
        raise VentaApiVersionError()

    async def init(self) -> None:
        """Initialize the Venta device."""
        data = await self.status()
        self.mac = data.header.get("MacAdress")
        try:
            self.device_type = VentaDeviceType(data.header.get("DeviceType"))
        except ValueError:
            self.device_type = VentaDeviceType.UNKNOWN

    async def status(self) -> VentaData:
        """Update the Venta device."""
        return await self._map_data(
            await self._strategy.get_status(self.endpoint_definition.status)
        )

    async def action(self, action: dict[str, str | int | bool]) -> VentaData:
        """Send action to the Venta device."""
        return await self._map_data(
            await self._strategy.send_action(self.endpoint_definition.action, action)
        )

    def _set_api_defaults(self, api_version: VentaApiVersion | int) -> None:
        """Set the api version defaults."""
        self.api_version = VentaApiVersion(api_version)
        self.endpoint_definition = API_VERSION_ENDPOINTS[self.api_version]

        host_definition = VentaApiHostDefinition(
            self.host, self.endpoint_definition.port
        )

        if self.api_version == VentaApiVersion.V0:
            self._strategy = VentaTcpStrategy(
                host_definition,
                VentaTcpHeader(self.mac, self.device_type.value),
            )
        else:
            self._strategy = VentaHttpStrategy(host_definition, self._session)

    async def _map_data(
        self, data: dict[str, str | int | bool]
    ) -> dict[str, str | int | bool] | None:
        """Map device response to data."""
        return VentaData(
            header=data.get("Header", {}),
            action=data.get("Action", {}),
            info=data.get("Info", {}),
            measure=data.get("Measure", {}),
        )


class VentaApi:
    """Keep the Venta instance in one place and centralize the update."""

    device: VentaDevice
    name: str

    def __init__(self, device: VentaDevice) -> None:
        """Initialize the Venta Handle."""
        self.device = device
        self.name = "Venta"

    async def async_update(self) -> VentaData:
        """Pull the latest data from Venta."""
        return await self.device.status()


class VentaDataUpdateCoordinator(DataUpdateCoordinator[VentaData]):
    """Define an object to hold Venta data."""

    api: VentaApi

    def __init__(self, hass: HomeAssistant, api: VentaApi) -> None:
        """Initialize data coordinator."""
        self.api = api

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=api.device.update_interval
        )

    async def _async_update_data(self) -> VentaData:
        """Update data via library."""
        _LOGGER.debug("Polling Venta device: %s", self.api.device.host)
        try:
            async with asyncio.timeout(30):
                return await self.api.async_update()
        except ClientConnectionError as error:
            _LOGGER.warning(
                "Connection failed for %s", self.api.device.host, exc_info=error
            )
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
