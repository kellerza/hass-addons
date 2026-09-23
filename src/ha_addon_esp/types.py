"""EskomSePush API v3 response types."""

from __future__ import annotations

from dataclasses import dataclass, field

from cattrs.preconf.json import make_converter

CONVERTER = make_converter()

URI = "https://developer.sepush.co.za/business/3.0"
API_AREA = f"{URI}/area"
API_SCHEDULE = f"{URI}/schedule"
API_AREAS_SEARCH = f"{URI}/areas_search"


@dataclass
class ScheduleRef:
    """Schedule reference on an area."""

    id: str
    type: str
    auto_enabled: bool = False


@dataclass
class Area:
    """Area metadata from /area or areas_search."""

    id: str = ""
    name: str = ""
    municipality: str = ""
    province: str = ""
    schedules: list[ScheduleRef] = field(default_factory=list)


@dataclass
class Event:
    """Upcoming loadshedding event."""

    start: str
    end: str
    note: str


@dataclass
class Slot:
    """Time slot within a stage block."""

    start: str
    end: str


@dataclass
class StageBlock:
    """Stage or load-reduction block for one day."""

    name: str
    slots: list[Slot] = field(default_factory=list)


@dataclass
class ScheduleDay:
    """One day in the calendar."""

    date: str
    name: str
    schedule: list[StageBlock] = field(default_factory=list)


@dataclass
class Calendar:
    """Full schedule calendar."""

    days: list[ScheduleDay] = field(default_factory=list)


@dataclass
class Schedule:
    """Combined schedule state persisted for an ESP area."""

    name: str = ""
    events: list[Event] = field(default_factory=list)
    schedule: Calendar = field(default_factory=Calendar)
    area: Area | None = None


@dataclass
class AreasSearch:
    """areas_search response."""

    areas: list[Area] = field(default_factory=list)


@dataclass
class RateLimit:
    """x-ratelimit-* response headers."""

    limit: int = 0
    remaining: int = 0
    used: int = 0
    reset: str = ""


def is_v3_area_id(area_id: str) -> bool:
    """Return whether area_id is a v3 area id (underscores)."""
    return "_" in area_id


def v2_schedule_id(area_id: str) -> str:
    """Map a v2 hyphenated area id to a v3 schedule id."""
    parts = area_id.rsplit("-", 1)
    return parts[0] if len(parts) > 1 else area_id


def pick_schedule_id(area: Area) -> str:
    """Pick the best schedule id for an area."""
    for ref in area.schedules:
        if ref.auto_enabled and ref.type == "loadshedding":
            return ref.id
    for ref in area.schedules:
        if ref.auto_enabled:
            return ref.id
    if area.schedules:
        return area.schedules[0].id
    msg = f"No schedules for area {area.id or area.name}"
    raise ValueError(msg)


def rate_limit_from_headers(headers: dict[str, str]) -> RateLimit | None:
    """Parse x-ratelimit-* headers."""
    if "x-ratelimit-limit" not in headers:
        return None
    return RateLimit(
        limit=int(headers.get("x-ratelimit-limit", 0)),
        remaining=int(headers.get("x-ratelimit-remaining", 0)),
        used=int(headers.get("x-ratelimit-used", 0)),
        reset=headers.get("x-ratelimit-reset", ""),
    )
