"""QS64."""

import asyncio

from colorama import Fore

from .addon.bridge import HassBridge
from .qsusb import QsUsb
from .qwikswitch import qs_decode


async def main_loop() -> None:
    """Run the QS64 USB HID interface."""
    qsusb = QsUsb()

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
