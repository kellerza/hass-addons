"""Main."""

import sys
import asyncio
import logging

from qsusb64.addon.options import OPT
from qsusb64 import VERSION
from qsusb64.main import main_loop
from colorama import init

_LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Entry point."""
    init(autoreset=True)
    _LOGGER.info("qsusb64 version: %s", VERSION)
    OPT.init_addon()
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("Ctrl-c...")
        sys.exit(0)


if __name__ == "__main__":
    main()
