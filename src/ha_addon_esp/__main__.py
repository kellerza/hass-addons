"""Main."""

import asyncio
import logging
import sys

import attrs
from mqtt_entity import MQTTClient
from mqtt_entity.options import MQTTOptions

from .esp import ESP, search_area

_LOG = logging.getLogger(__name__)


async def main_loop() -> int:
    """Entry point."""
    opt = Options()
    await opt.init_addon()

    if opt.search_area:
        await search_area(opt.search_area, opt.areas[0].api_key)

    if not opt.areas:
        _LOG.error("No areas to monitor. Check config")
        return 1

    asyncio.get_event_loop().set_debug(opt.debug > 0)
    devs = list[ESP]()
    client = MQTTClient(
        availability_topic="ESP/availability",
        devs=[],
        origin_name="ESP sensors for Home Assistant",
    )
    for area in opt.areas:
        devs.append(
            ESP(
                api_key=area.api_key,
                area_id=area.area_id,
                ha_prefix=area.ha_prefix,
                client=client,
            )
        )
    client.devs.extend([d.mqtt_dev for d in devs])

    await client.connect(opt)
    client.monitor_homeassistant_status()
    _LOG.info("Connected to MQTT broker")

    # wait a bit for discovery
    await asyncio.sleep(10)

    for dev in devs:
        await dev.init()

    wait = 60 * 5  # Initially wait 5 min for an update

    while True:
        try:
            await asyncio.sleep(wait)
            for dev in devs:
                await dev.callback(client)
        except asyncio.CancelledError:
            _LOG.info("Shutting down ESP sensors")
            break
        except Exception as ex:
            _LOG.exception("Error in main loop: %s", ex)
        wait = 60 * 60  # Update every hour
    return 0


@attrs.define()
class AreaOptions:
    """Options for an ESP area."""

    api_key: str = ""
    area_id: str = ""
    ha_prefix: str = ""


@attrs.define()
class Options(MQTTOptions):
    """HASS Addon Options."""

    areas: list[AreaOptions] = attrs.field(factory=list)
    search_area: str = ""
    debug: int = 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main_loop()))
