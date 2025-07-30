"""Options."""

import attrs
from mqtt_entity.options import MQTTOptions


@attrs.define()
class ControlGroupOptions:
    """Options for a control group."""

    name: str = ""
    entities: list[str] = attrs.field(factory=list)
    template: str = ""


@attrs.define()
class Options(MQTTOptions):
    """HASS Addon Options."""

    groups: list[ControlGroupOptions] = attrs.field(factory=list)
    ha_prefix: str = "cgroup"
    uuid: str = "b7e8f2e2-3c4d-4a2b-8c1a-9f6e7d5c2b1a"

    ha_api_url: str = ""
    ha_api_token: str = ""
    debug: int = 0
