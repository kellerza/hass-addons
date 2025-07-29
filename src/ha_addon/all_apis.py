"""All HA APIs."""

import asyncio

import attrs
from mqtt_entity import MQTTClient

from ha_addon.ha_api import HaRestApi, HaWebsocketApi, LogBase


@attrs.define()
class HaAllApis[T](LogBase):
    """API clients for the add-on."""

    opt: T = attrs.field(init=False, repr=False)
    rest: HaRestApi = attrs.field(default=None, init=False, repr=False)
    ws: HaWebsocketApi = attrs.field(default=None, init=False, repr=False)
    mqtt: MQTTClient = attrs.field(init=False, repr=False)

    _log_prefix = "HA APIs: "

    async def connect_rest_ws(self) -> None:
        """Bootstrap the API clients."""
        if self.rest is None:
            self.rest = HaRestApi().set_from_options(self.opt)
        if self.ws is None:
            self.ws = HaWebsocketApi().set_from_options(self.opt)

        # Check REST API
        time = 0
        while not await self.rest.is_running():
            if time < 30:
                time += 5
            self.log_error(
                f"API is not running: {self.rest.url} (token=...{self.rest.token[-10:]}). Retrying in {time} seconds."
            )
            await asyncio.sleep(time)

        # Check WS API
        self.ws.async_start_ws_loop()
        await self.ws.wait_authenticated()
        self.ws.ping(interval=10)

    async def close(self) -> None:
        """Close the API clients."""
        await self.rest.close()
        await self.ws.close()
        await self.mqtt.disconnect()
