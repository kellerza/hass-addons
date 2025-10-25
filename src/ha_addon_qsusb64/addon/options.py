"""Addon options."""

import logging
from functools import cached_property

import attrs
from mqtt_entity.options import MQTTOptions

from ..qwikswitch import parse_id, string_id

_LOG = logging.getLogger(__name__)


@attrs.define()
class DeviceOpt:
    """Options for an entity."""

    id: str = ""
    kind: str = ""
    name: str = ""

    def allok(self, checkname: bool = True) -> bool:
        """Check if the entity is empty."""
        if not self.id and not self.name and not self.kind:
            return False
        try:
            self.id = string_id(parse_id(self.id))
        except ValueError:
            _LOG.error("Invalid ID: %s, %s", self.id, self)
            return False
        if checkname and not self.name:
            _LOG.error("Invalid name: %s: %s", self.name, self)
            return False
        return True


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
                _LOG.error("Invalid button ID: %s", btn)
        return res


@attrs.define()
class Options(MQTTOptions):
    """Addon Options."""

    buttons: list[ButtonOpt] = attrs.field(factory=list)
    switches: list[DeviceOpt] = attrs.field(factory=list)
    lights: list[DeviceOpt] = attrs.field(factory=list)
    binary_sensors: list[DeviceOpt] = attrs.field(factory=list)
    sensors: list[DeviceOpt] = attrs.field(factory=list)

    ignore: list[DeviceOpt] = attrs.field(factory=list)

    debug: int = 0
    prefix: str = "qsusb64"

    def check_allok(self) -> None:
        """Remove entities with empty IDs."""
        self.switches = [o for o in self.switches if o.allok()]
        self.lights = [o for o in self.lights if o.allok()]
        self.binary_sensors = [o for o in self.binary_sensors if o.allok()]
        self.sensors = [o for o in self.sensors if o.allok()]
        self.ignore = [o for o in self.ignore if o.allok(checkname=False)]


OPT = Options()
