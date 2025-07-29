"""HA API types."""

from typing import Any

import attrs


@attrs.define()
class HAEvents:
    """Response from the get_events request.

    {
      "event": "state_changed",
      "listener_count": 5
    }
    """

    event: str = ""
    listener_count: int = 0


@attrs.define()
class HAService:
    """Response from the get_services request.

    {
      "domain": "light",
      "service": "turn_on"
    }
    """

    domain: str = ""
    service: list[str] = attrs.field(factory=list)


@attrs.define()
class HAState:
    """Response from a call_service request.

    {
        "attributes": {},
        "entity_id": "sun.sun",
        "last_changed": "2016-05-30T21:43:32.418320+00:00",
        "state": "below_horizon"
    }
    """

    entity_id: str
    state: str

    attributes: dict[str, Any] = attrs.field(factory=dict)
    context: dict[str, Any] = attrs.field(factory=dict)
    last_changed: str = ""
    last_reported: str = ""
    last_updated: str = ""
