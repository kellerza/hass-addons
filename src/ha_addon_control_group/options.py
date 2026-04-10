"""Options."""

import logging
from dataclasses import dataclass, field

from anyio import Path
from mqtt_entity.options import CONVERTER, MQTTOptions
from mqtt_entity.utils import slug
from yaml import safe_load

from ha_addon.all_apis import HaAllApis

_LOG = logging.getLogger(__name__)


@dataclass
class ControlGroupOptions:
    """Options for a control group."""

    id: str
    name: str = ""
    entities: list[str] = field(default_factory=list)
    template: str = ""
    call_script: str = ""

    def __post_init__(self) -> None:
        """Init."""
        self.id = slug(self.id).lower()
        if not self.id:
            raise ValueError("Group ID cannot be empty.")


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

    async def init_addon(self) -> None:
        """Init addon options."""
        await super().init_addon()

        haconfig = Path("/homeassistant/control_groups")
        if not await haconfig.parent.exists():
            _LOG.warning("Home Assistant config folder not found, fallback to /config")
            haconfig = Path("/config")
        await haconfig.mkdir(exist_ok=True, parents=True)

        files = [p async for p in haconfig.glob("group*.yml")]
        _LOG.info(
            "Found %d group config files (matching group*.yml): %s",
            len(files),
            ", ".join(p.name for p in files),
        )
        if not files:
            _LOG.warning("No group config files found in %s", haconfig)

        # Load others from files
        for path in files:
            _LOG.info("Loading group config from %s", path)
            try:
                fbytes = await path.read_bytes()
                data = safe_load(fbytes)
                res = CONVERTER.structure(data, list[ControlGroupOptions])
                self.groups.extend(res)
            except Exception as ex:
                _LOG.error("Error loading group config from %s: %s", path, ex)

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
