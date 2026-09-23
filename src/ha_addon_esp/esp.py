"""Sensors for ESP."""

from __future__ import annotations

import json
import logging
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import aiohttp
from mqtt_entity import MQTTClient, MQTTDevice, MQTTSensorEntity
from mqtt_entity.helpers import hass_share_path
from mqtt_entity.utils import slug

from .types import (
    API_AREA,
    API_AREAS_SEARCH,
    API_SCHEDULE,
    CONVERTER,
    Area,
    AreasSearch,
    RateLimit,
    Schedule,
    is_v3_area_id,
    pick_schedule_id,
    rate_limit_from_headers,
    v2_schedule_id,
)

_LOG = logging.getLogger(__name__)

ADDON_SLUG = "hass-addon-esp"


@dataclass
class QueryResult:
    """Result of an API query."""

    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    error: str = ""


@dataclass
class ESP:
    """ESP Class."""

    api_key: str
    area_id: str
    ha_prefix: str
    client: MQTTClient
    area: str = ""

    mqtt_dev: MQTTDevice = field(
        default_factory=lambda: MQTTDevice(
            identifiers=[""],
            components={},
            manufacturer="EskomSePush API",
        )
    )

    state: Schedule | None = None
    """State of the area."""
    statefile: Path = field(init=False)
    """Persistent storage for the area's state."""
    sensors: list[ESPSensor] = field(default_factory=list)
    rate_limit: RateLimit | None = None
    _schedule_id: str = ""

    def __post_init__(self) -> None:
        """Init."""
        self.statefile = (
            hass_share_path(ADDON_SLUG, True) / f"esp_{slug(self.area_id)}.json"
        )
        self.state = self._load_state()

        area_sensor = AreaSensor(name="Area")
        self.sensors = [
            area_sensor,
            NextSensor(name="Next"),
            AllowanceSensor(name="Allowance"),
        ]

        self.mqtt_dev.identifiers[0] = self.id()
        self.area = self._area_display_name()
        self.mqtt_dev.name = f"ESP area {self.area}"
        for sen in self.sensors:
            sen.init_entity(self.mqtt_dev, self.ha_prefix)

    def _load_state(self) -> Schedule | None:
        """Load persisted schedule state."""
        if not self.statefile.exists():
            return None
        _LOG.debug("Loading state from %s", self.statefile)
        with self.statefile.open(encoding="utf-8") as jsf:
            raw = json.load(jsf)
        if not isinstance(raw, dict) or "info" in raw:
            _LOG.info("Ignoring legacy v2 state file")
            return None
        try:
            state = CONVERTER.structure(raw, Schedule)
        except Exception as err:
            _LOG.warning("Could not load state: %s", err)
            return None
        if state.area:
            self._schedule_id = pick_schedule_id(state.area)
        return state

    def _save_state(self) -> None:
        """Persist schedule state."""
        if not self.state:
            return
        _LOG.debug("Saving state to %s", self.statefile)
        with self.statefile.open("w", encoding="utf-8") as jsf:
            json.dump(CONVERTER.unstructure(self.state), jsf, indent=2)

    def _area_display_name(self) -> str:
        """Human-readable area name for the MQTT device."""
        if self.state and self.state.area and self.state.area.name:
            return self.state.area.name
        if self.state and self.state.name:
            return self.state.name
        return self.area_id

    def id(self) -> str:
        """Return the identifiers for the ESP."""
        return f"eskomsp_{slug(self.area_id)}"

    async def query(self, uri: str, params: dict[str, Any]) -> QueryResult:
        """Query the API."""
        try:
            headers = {"token": self.api_key}
            async with aiohttp.ClientSession() as session:
                async with session.get(uri, headers=headers, params=params) as resp:
                    body = await resp.json(content_type=None)
                    hdrs = {k.lower(): v for k, v in resp.headers.items()}
                    if resp.status != 200:
                        err = (
                            body.get("error", resp.reason)
                            if isinstance(body, dict)
                            else resp.reason
                        )
                        _LOG.error("API %s %s: %s", resp.status, uri, err)
                        return QueryResult(
                            ok=False,
                            data=body if isinstance(body, dict) else {},
                            headers=hdrs,
                            error=str(err),
                        )
                    if isinstance(body, dict) and "error" in body:
                        _LOG.error("API error from %s: %s", uri, body["error"])
                        return QueryResult(
                            ok=False, data=body, headers=hdrs, error=str(body["error"])
                        )
                    return QueryResult(ok=True, data=body, headers=hdrs)
        except aiohttp.ClientError as err:
            _LOG.error("Read Error: %s: %s", type(err), err)
            return QueryResult(ok=False, error=str(err))

    async def _fetch_area(self) -> Area | None:
        """Fetch area metadata (once per area)."""
        res = await self.query(API_AREA, {"id": self.area_id})
        if not res.ok:
            return None
        self.rate_limit = rate_limit_from_headers(res.headers) or self.rate_limit
        return CONVERTER.structure(res.data, Area)

    async def _fetch_schedule(self, schedule_id: str) -> Schedule | None:
        """Fetch schedule events and calendar."""
        res = await self.query(API_SCHEDULE, {"id": schedule_id})
        if not res.ok:
            return None
        self.rate_limit = rate_limit_from_headers(res.headers) or self.rate_limit
        return CONVERTER.structure(res.data, Schedule)

    async def _resolve_schedule_id(self) -> str:
        """Resolve schedule id from config and cached area."""
        if self._schedule_id:
            return self._schedule_id
        if is_v3_area_id(self.area_id):
            area = (
                self.state.area
                if self.state and self.state.area
                else await self._fetch_area()
            )
            if not area:
                return ""
            self._schedule_id = pick_schedule_id(area)
            return self._schedule_id
        self._schedule_id = v2_schedule_id(self.area_id)
        return self._schedule_id

    async def query_api(self, *, fetch_area: bool = False) -> None:
        """Read schedule state from the API."""
        area: Area | None = self.state.area if self.state else None
        if fetch_area and is_v3_area_id(self.area_id):
            area = await self._fetch_area()
            if area:
                self._schedule_id = pick_schedule_id(area)

        schedule_id = await self._resolve_schedule_id()
        if not schedule_id:
            return

        schedule = await self._fetch_schedule(schedule_id)
        if not schedule:
            return
        if area:
            schedule.area = area
        self.state = schedule
        self.area = self._area_display_name()
        self.mqtt_dev.name = f"ESP area {self.area}"
        self._save_state()

    async def callback(self, client: MQTTClient) -> None:
        """ESP callback - run every hour."""
        try:
            if not self.state:
                await self.init()
                return
            _LOG.info("Updating ESP state")
            await self.query_api()
            for sen in self.sensors:
                await sen.get_state(self)
        except Exception:
            traceback.print_exc()
            raise

    async def init(self) -> None:
        """Initialize ESP."""
        if not self.state:
            _LOG.info("No state history, querying API")
            await self.query_api(fetch_area=True)
        else:
            _LOG.debug("Using state history: %s", self.state.name)

        for sen in self.sensors:
            await sen.get_state(self)


@dataclass
class ESPSensor:
    """Base class for ESP sensors."""

    name: str = field()
    entity: MQTTSensorEntity = field(init=False)

    def init_entity(self, dev: MQTTDevice, ha_prefix: str) -> None:
        """Init entity."""
        nme = slug(self.name)
        unique_id = f"{dev.id}_{nme}"
        self.entity = MQTTSensorEntity(
            unique_id=unique_id,
            name=self.name,
            state_topic=f"ESP/{unique_id}/state",
            json_attributes_topic=f"ESP/{unique_id}/attributes",
            default_entity_id=f"sensor.{ha_prefix}_{nme}",
        )
        dev.components[f"{ha_prefix}_{nme}"] = self.entity

    async def get_state(self, esp: ESP) -> Any:
        """Read the sensor value from the API."""
        raise NotImplementedError


@dataclass(slots=True)
class AreaSensor(ESPSensor):
    """Area name and metadata sensor."""

    async def get_state(self, esp: ESP) -> Any:
        """Publish area name and attributes."""
        if not esp.state:
            return None
        val = esp.state.area.name if esp.state.area else esp.state.name
        await self.entity.send_state(esp.client, val, retain=True)
        atr: dict[str, Any] = {
            "events": CONVERTER.unstructure(esp.state.events),
            "schedule": CONVERTER.unstructure(esp.state.schedule),
        }
        if esp.state.area:
            atr["province"] = esp.state.area.province
            atr["municipality"] = esp.state.area.municipality
        _LOG.debug("Attributes %s = %s", self.name, json.dumps(atr))
        await self.entity.send_json_attributes(esp.client, atr)
        return val


@dataclass(slots=True)
class NextSensor(ESPSensor):
    """Next loadshedding event sensor."""

    async def get_state(self, esp: ESP) -> Any:
        """Publish next event start time."""
        if not esp.state or not esp.state.events:
            return None
        event = esp.state.events[0]
        await self.entity.send_state(esp.client, event.start, retain=True)
        await self.entity.send_json_attributes(esp.client, CONVERTER.unstructure(event))
        return event.start


@dataclass(slots=True)
class AllowanceSensor(ESPSensor):
    """API credit allowance sensor."""

    async def get_state(self, esp: ESP) -> Any:
        """Publish remaining API credits from rate-limit headers."""
        rl = esp.rate_limit
        if not rl:
            return None
        await self.entity.send_state(esp.client, rl.remaining, retain=True)
        atr = {
            "count": rl.used,
            "limit": rl.limit,
            "remaining": rl.remaining,
            "reset": rl.reset,
        }
        await self.entity.send_json_attributes(esp.client, atr, retain=True)
        return rl.remaining


async def search_area(name: str, api_key: str) -> None:
    """Search for an area."""
    sfile = hass_share_path(ADDON_SLUG, True) / "esp_search.json"
    res: AreasSearch | None = None
    cached = False
    if sfile.exists():
        with sfile.open(encoding="utf8") as fjson:
            raw = json.load(fjson)
        if raw.get("text") == name:
            res = CONVERTER.structure(raw, AreasSearch)
            cached = True

    if not res:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                API_AREAS_SEARCH,
                headers={"token": api_key},
                params={"text": name},
            ) as resp:
                body = await resp.json(content_type=None)
                if resp.status != 200 or not isinstance(body, dict):
                    _LOG.error("Search failed: %s", body)
                    return
                res = CONVERTER.structure(body, AreasSearch)
                payload = CONVERTER.unstructure(res)
                payload["text"] = name
                with sfile.open("w", encoding="utf8") as fjson:
                    json.dump(payload, fjson)

    out = CONVERTER.unstructure(res)
    if cached:
        out["cached"] = True
    _LOG.info("Search result:\n%s", json.dumps(out, indent=2))
