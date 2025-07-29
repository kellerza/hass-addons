"""Options."""

import attrs
from mqtt_entity.options import MQTTOptions


@attrs.define()
class ControlGroupOptions:
    """Options for a control group."""

    name: str = ""
    entities: list[str] = attrs.field(factory=list)
    template: str = ""
    ha_prefix: str = ""
    triggers: list[str] = attrs.field(factory=list)
    """A list of triggers for the control group."""


@attrs.define()
class Options(MQTTOptions):
    """HASS Addon Options."""

    groups: list[ControlGroupOptions] = attrs.field(factory=list)
    debug: int = 0

    ha_api_url: str = ""
    ha_api_token: str = ""

    uuid: str = "b7e8f2e2-3c4d-4a2b-8c1a-9f6e7d5c2b1a"
