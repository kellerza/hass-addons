"""Addon options."""

import logging
from mqtt_entity.options import Options
from qsusb64.qwikswitch import parse_id, string_id
import attrs
from functools import cached_property

_LOGGER = logging.getLogger(__name__)


@attrs.define()
class DevOptions:
    """Options for an entity."""

    id: str = ""
    kind: str = ""
    name: str = ""


@attrs.define()
class Buttons:
    """Options for an entity."""

    name: str = ""
    buttons: list[str] = attrs.field(factory=list)

    @cached_property
    def button_dict(self) -> dict[str, str]:
        """Return a map of button ids and their names."""
        res: dict[str, str] = {}
        btnidx = 1
        for btn in self.buttons:
            try:
                id = string_id(parse_id(btn))
                if id in res:
                    continue
                res[id] = f"button_{btnidx}"
                btnidx = btnidx + 1
                continue
            except ValueError:
                pass
            try:
                ids, name = btn.split(":", 1)
                id = string_id(parse_id(ids))
                res[id] = name.strip()
            except ValueError:
                _LOGGER.error("Invalid button ID: %s", btn)
        return res


@attrs.define()
class QSOptions(Options):
    """Addon Options."""

    devices: list[DevOptions] = attrs.field(factory=list)


OPT = QSOptions()
