"""Control group discovery from Home Assistant helper metadata."""

import logging
from dataclasses import dataclass, field
from typing import Any

from mqtt_entity.utils import slug

from ha_addon.all_apis import HaAllApis
from ha_addon.ha_api.types import HAState

_LOG = logging.getLogger(__name__)


@dataclass
class ControlGroupOptions:
    """Options for a control group."""

    id: str
    name: str = ""
    src_entity: str = ""
    entities: list[str] = field(default_factory=list)
    template: str = ""
    call_script: str = ""

    def __post_init__(self) -> None:
        """Init."""
        self.id = slug(self.id).lower()
        if not self.id:
            raise ValueError("Group ID cannot be empty.")


async def discover_control_groups(
    api: HaAllApis[Any],
    *,
    tag: str = "control_group",
) -> list[ControlGroupOptions]:
    """Discover control groups from tagged template sensor helpers."""
    await api.connect_rest_ws()

    states = await api.rest.get_states()
    registry = await api.ws.get_entity_registry()

    _LOG.error(
        [
            (t.entity_id, t.platform, t.labels)
            for t in registry
            if t.platform == "template"
        ]
    )

    registry_map = {
        r.entity_id: r
        for r in registry
        if r.entity_id.startswith("sensor.")
        and (r.platform == "template")
        and tag in r.labels
    }
    state_map = {s.entity_id: s for s in states if isinstance(s.entity_id, str)}

    if not registry_map:
        _LOG.warning("No tagged template sensor helpers found for tag '%s'.", tag)

    groups: list[ControlGroupOptions] = []
    for eid, reg in registry_map.items():
        group = _to_group(state_map[eid])
        if not group:
            _LOG.warning("Skipping helper with invalid entity id: %s", eid)
            continue
        _LOG.warning("Getting template for config entry %s", reg.config_entry_id)
        group.template = await api.rest.get_config_entry_template(reg.config_entry_id)
        _LOG.info(group.template)

        if not group.entities:
            _LOG.warning(
                "Helper '%s' has no target entities (expected attribute like entities/control_group_entities).",
                reg.entity_id,
            )
        groups.append(group)

    _LOG.info(
        "Loaded %d control groups from HA template helpers tagged '%s'.",
        len(groups),
        tag,
    )
    return groups


def _to_group(state: HAState) -> ControlGroupOptions | None:
    """Convert a helper state to a control-group option object."""
    _, _, raw_id = state.entity_id.partition(".")
    raw_id = raw_id.strip()
    if not raw_id:
        return None

    target = state.entity_id.replace("sensor.", "light.")
    if target.endswith("_state"):
        target = target[:-6]
    else:
        _LOG.warning(
            "Helper '%s' does not follow expected naming convention (should end with '_state'). Skipping.",
            state.entity_id,
        )
        return None

    # If you want to store something in attributes, yaml overrides
    attrs = state.attributes or {}

    # call_script = str(
    #     attrs.get("control_group_call_script") or attrs.get("call_script") or ""
    # ).strip()

    # Use helper state as template source by default.
    # template = str(attrs.get("control_group_template") or "").strip()
    # if not template:
    #     template =

    return ControlGroupOptions(
        id=raw_id,
        name=str(attrs.get("friendly_name") or "").strip(),
        src_entity=state.entity_id,
        entities=[target],
        template="{{ states('" + state.entity_id + "') }}",
        # call_script=call_script,
    )
