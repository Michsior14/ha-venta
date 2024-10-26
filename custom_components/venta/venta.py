"""Venta data and api classes."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum

from aiohttp import ClientConnectionError, ClientError, ClientSession
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
    LP60 = 1
    LPH60 = 2
    LW60 = 3
    LW60T = 4
    LW62 = 5
    LW62T = 6
    AP902 = 11
    AH902 = 12
    AW902 = 13
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

    method: str
    url: str


@dataclass
class VentaApiDefinition:
    """Venta api definition."""

    version: VentaApiVersion
    status: VentaApiEndpointDefinition
    action: VentaApiEndpointDefinition | None
    port: int = 80

    @property
    def id(self) -> str:
        """Return the id of the definition."""
        status_id = self.status.url
        action_id = self.action.url if self.action else "None"
        return f"{self.version.value}/{status_id}/{action_id}"


API_DEFINITIONS: list[VentaApiDefinition] = [
    VentaApiDefinition(
        VentaApiVersion.V3,
        VentaApiEndpointDefinition("POST", "api/telemetry"),
        VentaApiEndpointDefinition("POST", "api/telemetry?request=set"),
    ),
    VentaApiDefinition(
        VentaApiVersion.V3, VentaApiEndpointDefinition("GET", "sensordata.json"), None
    ),
    VentaApiDefinition(
        VentaApiVersion.V2,
        VentaApiEndpointDefinition("POST", "datastructure"),
        VentaApiEndpointDefinition("POST", "datastructure"),
    ),
    VentaApiDefinition(
        VentaApiVersion.V0,
        VentaApiEndpointDefinition("GET", "Complete"),
        VentaApiEndpointDefinition("POST", "Action"),
        48000,
    ),
]


@dataclass
class VentaData:
    """Class for holding the Venta data."""

    header: dict[str, str | int | bool] = field(default_factory=dict)
    action: dict[str, str | int | bool] = field(default_factory=dict)
    info: dict[str, str | int | bool] = field(default_factory=dict)
    measure: dict[str, str | int | bool] = field(default_factory=dict)
    is_empty: bool = field(default=False)


class VentaDevice:
    """Representation of a Venta device."""

    host: str
    mac: str | None
    device_type: VentaDeviceType
    api_version: VentaApiVersion
    update_interval: timedelta
    api_definition: VentaApiDefinition

    def __init__(
        self,
        host: str,
        update_interval: timedelta,
        api_definition_id: str | None,
        session: ClientSession | None = None,
    ) -> None:
        """Venta device constructor."""
        self.host = host
        self.update_interval = update_interval
        self.mac = None
        self.device_type = VentaDeviceType.UNKNOWN
        self._session = session
        self._endpoint_definition = None
        self._strategy = None

        if api_definition_id is not None:
            api_definition = next(
                (d for d in API_DEFINITIONS if d.id == api_definition_id),
                None,
            )
            if api_definition is None:
                raise ValueError(f"Api definition {api_definition_id} not found.")
            self._set_api_definition(api_definition)

    async def detect_api(self, api_version: int | None = None) -> None:
        """Detect the venta api."""
        definitions = API_DEFINITIONS
        if api_version is not None:
            definitions = [d for d in definitions if d.version.value == api_version]

        for api_definition in definitions:
            self._set_api_definition(api_definition)
            try:
                status = self.api_definition.status
                async with asyncio.timeout(5):
                    data = await self._strategy.get_status(
                        status.method,
                        status.url,
                    )
                    if data is not None and data.get("Header") is not None:
                        return
                await asyncio.sleep(0.5)
            except (asyncio.TimeoutError, ClientError):
                pass
        raise VentaApiVersionError()

    async def init(self) -> None:
        """Initialize the Venta device."""
        data = await self.status()
        self.mac = data.header.get("MacAdress") or data.header.get("DeviceId")

        try:
            self.device_type = VentaDeviceType(data.header.get("DeviceType"))
        except ValueError:
            self.device_type = VentaDeviceType.UNKNOWN

        if isinstance(self._strategy, VentaTcpStrategy):
            self._strategy.set_header(
                VentaTcpHeader(
                    mac=self.mac,
                    device_type=self.device_type.value,
                )
            )

    async def status(self) -> VentaData:
        """Update the Venta device."""
        return await self._map_data(
            await self._strategy.get_status(
                self.api_definition.status.method, self.api_definition.status.url
            )
        )

    async def action(
        self,
        action: dict[str, str | int | bool],
        coordinator: "VentaDataUpdateCoordinator",
    ) -> VentaData:
        """Send action to the Venta device."""
        if self.api_definition.action is None:
            raise ValueError("Action is not supported for this device.")

        data = await self._map_data(
            await self._strategy.send_action(
                self.api_definition.action.method,
                self.api_definition.action.url,
                action,
            )
        )

        await asyncio.sleep(0.2)  # Wait for the device to process the action
        await coordinator.async_request_refresh()

        return data

    def _set_api_definition(self, api_definition: VentaApiDefinition) -> None:
        """Set the api definition defaults."""
        self.api_version = api_definition.version
        self.api_definition = api_definition

        host_definition = VentaApiHostDefinition(self.host, self.api_definition.port)
        if self.api_version == VentaApiVersion.V0:
            self._strategy = VentaTcpStrategy(host_definition)
        else:
            self._strategy = VentaHttpStrategy(host_definition, self._session)

    async def _map_data(self, data: dict[str, str | int | bool] | None) -> VentaData:
        """Map device response to data."""
        if data is None:
            return VentaData(is_empty=True)

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
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=api.device.update_interval
        )
        self.api = api
        self.data = VentaData()

    async def _async_update_data(self) -> VentaData:
        """Update data via library."""
        _LOGGER.debug("Polling Venta device: %s", self.api.device.host)
        try:
            data = await self.api.async_update()
            if data.is_empty:
                _LOGGER.debug("Venta device: %s not updated", self.api.device.host)
            else:
                self.data = data
            return self.data
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
