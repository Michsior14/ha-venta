"""Venta data and api classes."""
import logging
from datetime import timedelta
import asyncio
from dataclasses import dataclass

from aiohttp import ClientConnectionError
from aiohttp import ClientSession, ServerDisconnectedError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import UNKNOWN_DEVICE_TYPE, DOMAIN, TIMEOUT

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=10)

DEVICE_TYPES = {106: "LW73/LW74"}


@dataclass
class VentaData:
    """Class for holding the Venta data."""

    header: dict[str, str | int]
    action: dict[str, str | int]
    info: dict[str, str | int]
    measure: dict[str, str | int]


class VentaDevice:
    """Representation of a Venta device."""

    def __init__(self, host, session=None) -> None:
        """Venta device constructor."""
        self.host = host
        self.mac = None
        self.device_type = None
        self._session = session

    async def init(self):
        """Initialize the Venta device."""
        data = await self.update()
        self.mac = data.header.get("MacAdress")
        self.device_type = DEVICE_TYPES.get(
            data.header.get("DeviceType"), UNKNOWN_DEVICE_TYPE
        )

    async def update(self, json_action=None):
        """Update the Venta device."""
        data = await self._get_data(json_action)
        return VentaData(
            header=data.get("Header", {}),
            action=data.get("Action", {}),
            info=data.get("Info", {}),
            measure=data.get("Measure", {}),
        )

    async def _get_data(self, json_action=None, retries=3):
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

    async def _run_get_data(self, json=None):
        """Make the http request."""
        _LOGGER.debug("Sending update request with data: %s", str(json))
        async with self._session.post(
            f"http://{self.host}/datastructure", json=json
        ) as resp:
            return await resp.json(content_type="text/plain")


class VentaApi:
    """Keep the Venta instance in one place and centralize the update."""

    def __init__(self, device: VentaDevice) -> None:
        """Initialize the Venta Handle."""
        self.device = device
        self.name = "Venta"
        self.host = device.host

    async def async_update(self, **kwargs) -> VentaData:
        """Pull the latest data from Venta."""
        return await self.device.update()


class VentaDataUpdateCoordinator(DataUpdateCoordinator[VentaData]):
    """Define an object to hold Venta data."""

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
        return DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, device.mac)},
            manufacturer="Venta",
            name=f"Venta {device.device_type}",
            model=device.device_type,
            sw_version=self.data.info.get("SWMain"),
        )
