"""QS64."""

import hid  # type: ignore
import asyncio
from colorama import Fore
from qsusb64.qwikswitch import qs_decode, qs_encode, l2s
from qsusb64.helpers import listen


async def set_dev(dev: hid.device, delay: int, msg: str, data: list[int]) -> None:
    """Sleep and write data to the device."""
    # print("Waiting for", delay, "seconds before writing data")
    await asyncio.sleep(delay)
    print(f"TX {Fore.GREEN}{msg}", l2s(data))
    # pad data to 64 bytes
    data = [2] + [*data]
    data += [0x0] * (64 - len(data))
    assert len(data) == 64, "Data must be 64 bytes long"

    dev.write(data)


async def main_loop() -> None:
    dev = hid.device()
    try:
        dev.open(0x04D8, 0x2005)
    except OSError as e:
        print(f"Error opening device: {e}")
        return
    print("Manufacturer: %s" % dev.get_manufacturer_string())
    print("Product: %s" % dev.get_product_string())

    # enable non-blocking mode
    dev.set_nonblocking(1)

    listen("192.168.1.8")

    asyncio.create_task(set_dev(dev, 2, "btn 0", qs_encode("TOGGLE", "@1cbd31", 7)))

    # asyncio.create_task(set_dev(dev, 1, "bed 0", qs_encode("SET", "@288400", 50)))
    # asyncio.create_task(set_dev(dev, 1, "bed 0", qs_encode("SET", "@288400", 50)))
    # # asyncio.create_task(set_dev(dev, 5, "bed 5", qs_encode("SET", "@288400", 5)))
    # # asyncio.create_task(set_dev(dev, 13, "bed 100", qs_encode("SET", "@288400", 100)))

    # asyncio.create_task(set_dev(dev, 2, "dining off", qs_encode("SET", "@30e270", 0)))
    # asyncio.create_task(set_dev(dev, 12, "dining on", qs_encode("SET", "@30e270", 100)))

    # read back the answer
    try:
        while True:
            data: list[int] = dev.read(64)
            if data:
                print(f"RX {Fore.YELLOW}{qs_decode(data)}")

            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        dev.close()


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("Ctrl-c...")
