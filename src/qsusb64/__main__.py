"""Main."""

import asyncio
import logging

from qsusb64.addon.options import OPT
from qsusb64 import VERSION
from qsusb64.main import main_loop

_LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Entry point."""
    OPT.init_addon()
    _LOGGER.info("qsusb64 version: %s", VERSION)
    asyncio.run(main_loop())


if __name__ == "__main__":
    main()
