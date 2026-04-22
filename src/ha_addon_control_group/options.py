"""Options."""

import logging
from dataclasses import dataclass, field

from mqtt_entity.options import MQTTOptions
from mqtt_entity.utils import slug

from ha_addon.all_apis import HaAllApis
from ha_addon_control_group.options_discover import ControlGroupOptions

from .options_discover import discover_control_groups

_LOG = logging.getLogger(__name__)


@dataclass
class Options(MQTTOptions):
    """HASS Addon Options."""

    name: str = ""
    groups: list[ControlGroupOptions] = field(default_factory=list)
    ha_prefix: str = "cgroup"
    ha_api_url: str = ""
    ha_api_token: str = ""
    debug: int = 0

    def __post_init__(self) -> None:
        """Init."""
        self.ha_prefix = slug(self.ha_prefix).lower()
        if not self.ha_prefix:
            raise ValueError("HA prefix cannot be empty.")

    async def discover_groups(self) -> None:
        """Discover groups."""
        self.groups = await discover_control_groups(API)

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

        self.groups.sort(key=lambda g: g.id)


API = HaAllApis[Options]()
