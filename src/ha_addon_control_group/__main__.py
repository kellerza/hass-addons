"""Control group add-on."""

import asyncio
import logging
import sys

from .cbridge import STATE, CGroupBridge
from .options import API, Options
from .options_file import OPT_FILE

_LOG = logging.getLogger(__name__)


async def main_loop() -> int:
    """Entry point."""
    API.opt = Options()
    await API.opt.init_addon()

    OPT_FILE.load_file()

    STATE.cgs = [CGroupBridge(opt=g) for g in API.opt.groups]

    await API.connect_rest_ws()
    for cg in STATE.cgs:
        await cg.expand_entities()
    await STATE.websocket_on_connect()  # register templates

    await STATE.connect_mqtt()

    try:
        while True:
            try:
                await asyncio.sleep(0.2)

                if not API.ws.connected:
                    await asyncio.sleep(2)
                    _LOG.info("Websocket not connected, reconnecting...")
                    await API.connect_rest_ws()
                    await STATE.websocket_on_connect()

                await STATE.run_loop()

            except asyncio.CancelledError:
                _LOG.info("Shutting down cgroup sensors")
                break
            except Exception as ex:
                _LOG.error("Error in main loop: %s", ex, exc_info=True)
    finally:
        await API.close()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main_loop()))
