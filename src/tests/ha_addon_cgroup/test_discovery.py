"""Tests for control-group discovery loading."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from ha_addon.ha_api.types import HAEntity, HAState
from ha_addon_control_group.options_discover import discover_control_groups


@dataclass
class FakeRest:
    """Fake Home Assistant REST client for discovery tests."""

    states: list[HAState] = field(default_factory=list)

    async def get_states(self) -> list[HAState]:
        """Return preconfigured entity states."""
        return self.states

    async def get_config_entry_template(self, config_entry_id: str) -> str:
        """Return a placeholder template."""
        return "template"


@dataclass
class FakeWs:
    """Fake Home Assistant websocket client for discovery tests."""

    registry: list[HAEntity] = field(default_factory=list)

    async def get_entity_registry(self) -> list[HAEntity]:
        """Return preconfigured entity registry entries."""
        return self.registry


@dataclass
class FakeApi:
    """Minimal API stub for discover_control_groups tests."""

    rest: FakeRest
    ws: FakeWs

    async def connect_rest_ws(self) -> None:
        """No-op connect."""


@pytest.mark.asyncio
async def test_discovery_skips_disabled_helper_without_state() -> None:
    """Tagged registry entry without a state machine entry must not crash."""
    api = FakeApi(
        rest=FakeRest(states=[]),
        ws=FakeWs(
            registry=[
                HAEntity(
                    entity_id="sensor.test_light_state",
                    platform="template",
                    area_id="",
                    labels=["control_group"],
                    disabled_by="user",
                )
            ]
        ),
    )

    groups = await discover_control_groups(api)  # type: ignore[arg-type]

    assert groups == []
