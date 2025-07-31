"""Test the control group add-on.

uv run python -m ha_addon_control_group.test
"""

import asyncio
import logging
import sys
from collections.abc import Callable
from typing import Any

from ha_addon.all_apis import HaAllApis

from .options import Options

_LOG = logging.getLogger(__name__)

TEM1 = "{{ states('sun.sun') }}"


API = HaAllApis[Options]()


def ws_log_factory(template: str) -> Callable[[str, dict[str, Any]], None]:
    """Log factory."""

    def log(msg: str, obj: dict[str, Any]) -> None:
        _LOG.info(
            "  WS Rendered %s -> \n  result: %s\n  listeners: %s",
            template,
            msg,
            obj.get("listeners", ""),
        )

    return log


async def main_loop() -> int:
    """Entry point."""
    opt = API.opt = Options()
    await opt.init_addon()
    await API.connect_rest_ws()

    # Templates!
    res = await API.rest.render_template(TEM1)
    _LOG.info("REST Rendered %s ->\n  result: %s", TEM1, res)
    await API.ws.render_template(TEM1, ws_log_factory(TEM1))

    await asyncio.sleep(1)

    templ = "{{ states.binary_sensor | map(attribute='entity_id') | select('is_state', 'on') | list }}"
    bs = await API.rest.render_template(templ)
    _LOG.info("REST Rendered %s ->\n  result: %s", templ, bs)

    # Wait until Ctrl-C
    await asyncio.Event().wait()
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main_loop()))
