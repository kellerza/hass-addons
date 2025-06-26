"""QsUsb HID interface."""

from collections.abc import Callable
from typing import Any

import attrs
import hid  # type: ignore
from colorama import Fore

from .qwikswitch import QsMsg, l2s

type QsWrite = Callable[[QsMsg], None]


@attrs.define()
class QsUsb:
    """Connect to the QsUsb device."""

    dev: Any = attrs.field(init=False, repr=False)
    vid_pid: tuple[int, int] = (0x04D8, 0x2005)

    def __attrs_post_init__(self) -> None:
        """Connect."""
        self.dev = hid.device()
        try:
            self.dev.open(*self.vid_pid)
        except OSError as e:
            raise RuntimeError(f"Could not open QSUSB device {self.vid_pid}") from e
        print(f"Manufacturer: {self.dev.get_manufacturer_string()}")
        print(f"Product: {self.dev.get_product_string()}")
        self.dev.set_nonblocking(1)  # enable non-blocking mode

    def write(self, data: QsMsg, cmd: int = 0) -> None:
        """Write data to the HID device. Pad to 64 bytes."""
        print(f"TX {Fore.GREEN}{l2s(data)}")
        # pad data to 64 bytes
        data = [cmd, *data]
        data += [0] * (64 - len(data))
        assert len(data) == 64, "Data must be 64 bytes long"
        self.dev.write(data)

    def read(self, size: int = 12) -> QsMsg:
        """Read data from the HID device."""
        data = self.dev.read(64)
        if not data:
            return []
        return data[:size]

    def close(self) -> None:
        """Close the HID device."""
        self.dev.close()
