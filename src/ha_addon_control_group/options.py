"""Options."""

import logging

import attrs
from mqtt_entity.options import MQTTOptions
from mqtt_entity.utils import slug

from ha_addon.all_apis import HaAllApis

_LOG = logging.getLogger(__name__)


@attrs.define()
class ControlGroupOptions:
    """Options for a control group."""

    id: str = attrs.field(
        validator=lambda _, __, v: v == slug(v).lower() and len(v) > 0
    )
    name: str = ""
    entities: list[str] = attrs.field(factory=list)
    template: str = ""
    call_script: str = ""


@attrs.define()
class Options(MQTTOptions):
    """HASS Addon Options."""

    name: str = ""
    groups: list[ControlGroupOptions] = attrs.field(factory=list)
    ha_prefix: str = attrs.field(
        default="cgroup", validator=lambda _, __, v: v == slug(v).lower() and len(v) > 0
    )
    ha_api_url: str = ""
    ha_api_token: str = ""
    debug: int = 0

    async def init_addon(self) -> None:
        """Init addon options."""
        await super().init_addon()

        ids = [g.id for g in self.groups]
        if "" in ids:  # check empty IDs
            raise ValueError("Groups need a unique ID. Fix your config.")
        for r_id in ("status", "debug"):  # check for reserved IDs
            if r_id in ids:
                raise ValueError(f"Group ID '{r_id}' reserved. Fix your config.")
        if len(ids) != len(set(ids)):  # check duplicate IDs
            for aid in set(ids):
                ids.remove(aid)
            raise ValueError(f"Duplicate group IDs found: {ids}")


API = HaAllApis[Options]()
