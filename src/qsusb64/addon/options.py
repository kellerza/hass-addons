"""Addon options."""

import logging
from functools import cached_property

import attrs
from mqtt_entity.options import MQTTOptions

from ..qwikswitch import parse_id, string_id

_LOGGER = logging.getLogger(__name__)


@attrs.define()
class DeviceOpt:
    """Options for an entity."""

    id: str = ""
    kind: str = ""
    name: str = ""


@attrs.define()
class ButtonOpt:
    """Options for an entity."""

    name: str = ""
    buttons: list[str] = attrs.field(factory=list)
    model: str = ""

    @cached_property
    def btn_map(self) -> dict[str, str]:
        """Map button IDs to names."""
        res = dict[str, str]()
        btnidx = 1
        for btn in self.buttons:
            try:
                qid = string_id(parse_id(btn))
                if qid in res:
                    continue
                res[qid] = f"button_{btnidx}"
                btnidx = btnidx + 1
                continue
            except ValueError:
                pass
            try:
                ids, name = btn.split(":", 1)
                qid = string_id(parse_id(ids))
                res[qid] = name.strip()
            except ValueError:
                _LOGGER.error("Invalid button ID: %s", btn)
        return res


@attrs.define()
class Options(MQTTOptions):
    """Addon Options."""

    buttons: list[ButtonOpt] = attrs.field(factory=list)
    switches: list[DeviceOpt] = attrs.field(factory=list)
    lights: list[DeviceOpt] = attrs.field(factory=list)
    debug: int = 0
    prefix: str = "qsusb64_prefix"


OPT = Options()
