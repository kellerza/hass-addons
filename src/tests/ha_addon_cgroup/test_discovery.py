"""Tests for control-group discovery loading."""

# from __future__ import annotations

# from collections.abc import Generator
# from dataclasses import dataclass, field
# from typing import Any, cast

# import pytest
# from mqtt_entity.options import MQTTOptions

# from ha_addon.ha_api.types import HAState
# from ha_addon_control_group.options import API, Options


# @dataclass
# class FakeRest:
#     """Fake Home Assistant REST client for discovery tests."""

#     states: list[HAState] = field(default_factory=list)

#     def set_from_options(self, _opt: object) -> FakeRest:
#         """Mimic API signature and keep this fake instance."""
#         return self

#     async def get_states(self) -> list[HAState]:
#         """Return preconfigured entity states."""
#         return self.states


# @dataclass
# class FakeWs:
#     """Fake Home Assistant websocket client for discovery tests."""

#     registry: list[dict[str, Any]] = field(default_factory=list)

#     async def get_entity_registry(self) -> list[dict[str, Any]]:
#         """Return preconfigured entity registry entries."""
#         return self.registry


# @pytest.fixture(autouse=True)
# def _reset_api_clients() -> Generator[None]:
#     """Reset global API state between tests."""
#     API.rest = cast(Any, None)
#     API.ws = cast(Any, None)
#     yield
#     API.rest = cast(Any, None)
#     API.ws = cast(Any, None)


# @pytest.fixture(autouse=True)
# def _mock_mqtt_base_init(monkeypatch: pytest.MonkeyPatch) -> None:
#     """Avoid dependency on runtime addon environment in tests."""

#     async def _noop(self: MQTTOptions) -> None:
#         return None

#     monkeypatch.setattr(MQTTOptions, "init_addon", _noop)


# @pytest.fixture(autouse=True)
# def _mock_api_connect(monkeypatch: pytest.MonkeyPatch) -> None:
#     """Avoid network bootstrap in discovery tests."""

#     async def _noop() -> None:
#         return None

#     monkeypatch.setattr(API, "connect_rest_ws", _noop)


# @pytest.mark.asyncio
# async def test_discovery_loads_tagged_template_helpers() -> None:
#     """Tagged template sensor helpers are mapped to control groups."""
#     API.rest = cast(
#         Any,
#         FakeRest(
#             states=[
#                 HAState(
#                     entity_id="sensor.patio_group",
#                     state="on,motion",
#                     attributes={
#                         "friendly_name": "Patio Group",
#                         "entities": ["light.patio", "switch.patio"],
#                         "call_script": "script.notify_group",
#                     },
#                 )
#             ]
#         ),
#     )
#     API.ws = cast(
#         Any,
#         FakeWs(
#             registry=[
#                 {
#                     "entity_id": "sensor.patio_group",
#                     "platform": "template",
#                     "labels": ["control_group"],
#                 }
#             ]
#         ),
#     )

#     opt = Options()
#     await opt.init_addon()

#     assert [g.id for g in opt.groups] == ["patio_group"]
#     assert opt.groups[0].name == "Patio Group"
#     assert opt.groups[0].entities == ["light.patio", "switch.patio"]
#     assert opt.groups[0].call_script == "script.notify_group"
#     assert opt.groups[0].template == "{{ states('sensor.patio_group') }}"


# @pytest.mark.asyncio
# async def test_discovery_fallback_to_state_tags_when_registry_missing() -> None:
#     """State attributes are used when registry metadata is not available."""
#     API.rest = cast(
#         Any,
#         FakeRest(
#             states=[
#                 HAState(
#                     entity_id="sensor.kitchen_group",
#                     state="off",
#                     attributes={
#                         "friendly_name": "Kitchen",
#                         "tags": ["control group"],
#                         "entities": "light.kitchen,switch.kitchen_fan",
#                     },
#                 )
#             ]
#         ),
#     )
#     API.ws = cast(Any, FakeWs(registry=[]))

#     opt = Options()
#     await opt.init_addon()

#     assert [g.id for g in opt.groups] == ["kitchen_group"]
#     assert opt.groups[0].entities == ["light.kitchen", "switch.kitchen_fan"]


# @pytest.mark.asyncio
# async def test_discovery_ignores_non_template_registry_entries() -> None:
#     """Only template sensor helpers are selected from registry metadata."""
#     API.rest = cast(
#         Any,
#         FakeRest(
#             states=[
#                 HAState(
#                     entity_id="sensor.control_sensor",
#                     state="on",
#                     attributes={"labels": ["control group"]},
#                 ),
#                 HAState(
#                     entity_id="sensor.template_group",
#                     state="on",
#                     attributes={"entities": ["light.one"]},
#                 ),
#             ]
#         ),
#     )
#     API.ws = cast(
#         Any,
#         FakeWs(
#             registry=[
#                 {
#                     "entity_id": "sensor.control_sensor",
#                     "platform": "mqtt",
#                     "labels": ["control_group"],
#                 },
#                 {
#                     "entity_id": "sensor.template_group",
#                     "platform": "template",
#                     "labels": ["control_group"],
#                 },
#             ]
#         ),
#     )

#     opt = Options()
#     await opt.init_addon()

#     assert [g.id for g in opt.groups] == ["template_group"]


# @pytest.mark.asyncio
# async def test_discovery_keeps_reserved_id_validation() -> None:
#     """Existing validation rules still apply to API-loaded groups."""
#     API.rest = cast(
#         Any,
#         FakeRest(
#             states=[
#                 HAState(
#                     entity_id="sensor.status",
#                     state="on",
#                     attributes={"labels": ["control_group"]},
#                 )
#             ]
#         ),
#     )
#     API.ws = cast(
#         Any,
#         FakeWs(
#             registry=[
#                 {
#                     "entity_id": "sensor.status",
#                     "platform": "template",
#                     "labels": ["control_group"],
#                 }
#             ]
#         ),
#     )

#     opt = Options()

#     with pytest.raises(ValueError, match="reserved"):
#         await opt.init_addon()
