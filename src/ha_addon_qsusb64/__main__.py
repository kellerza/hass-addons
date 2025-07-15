"""Main."""

import asyncio
import sys

from colorama import Fore

from ha_addon.helpers import get_mqtt_details, logging_color

from .addon.bridge import HassBridge
from .addon.options import OPT
from .qsusb import QsUsb
from .qwikswitch import qs_decode


async def main_loop() -> int:
    """Run the QS64 USB HID interface."""
    OPT.init_addon()
    logging_color()
    await get_mqtt_details(OPT)

    try:
        qsusb = QsUsb()
    except ConnectionError:
        return 2

    hass = HassBridge(qs_write=qsusb.write)
    await hass.mqtt_connect()

    try:
        while True:
            data: list[int] = qsusb.read()
            if data:
                qsd = qs_decode(data)
                print(f"RX {Fore.YELLOW}{qsd}")
                if qid := qsd.get("id"):
                    try:
                        _, br = hass.find_id(qid)
                        await br.process_msg(qsd, hass.client)
                    except ValueError as e:
                        print(f"{Fore.RED}Error processing message: {e}")

            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        qsusb.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main_loop()))
