"""Test ESP v3 API types."""

from ha_addon_esp.types import (
    CONVERTER,
    Area,
    Event,
    Schedule,
    ScheduleRef,
    pick_schedule_id,
    v2_schedule_id,
)

AREA_EXAMPLE = {
    "id": "za_gt_jhb_orlandoeast_bi73",
    "municipality": "City of Johannesburg",
    "name": "Orlando East",
    "province": "Gauteng",
    "schedules": [
        {"auto_enabled": True, "id": "eskde-14", "type": "loadshedding"},
        {"id": "eskde-6", "type": "loadshedding"},
        {"auto_enabled": True, "id": "eskomgautenglr-f", "type": "load_reduction"},
    ],
}

SCHEDULE_EXAMPLE = {
    "events": [
        {
            "end": "2026-08-08T22:30:00+02:00",
            "note": "Stage 2",
            "start": "2026-08-08T20:00:00+02:00",
        }
    ],
    "name": "Eskom Direct Block 10",
    "schedule": {
        "days": [
            {
                "date": "2026-11-18",
                "name": "Tuesday",
                "schedule": [
                    {
                        "name": "Stage 1",
                        "slots": [
                            {
                                "end": "2026-11-18T20:30:00+02:00",
                                "start": "2026-11-18T18:00:00+02:00",
                            }
                        ],
                    }
                ],
            }
        ]
    },
}


def test_structure_area_example() -> None:
    """OpenAPI area payload structures cleanly."""
    area = CONVERTER.structure(AREA_EXAMPLE, Area)
    assert area.name == "Orlando East"
    assert len(area.schedules) == 3


def test_structure_schedule_example() -> None:
    """OpenAPI schedule payload structures cleanly."""
    schedule = CONVERTER.structure(SCHEDULE_EXAMPLE, Schedule)
    assert schedule.name == "Eskom Direct Block 10"
    assert isinstance(schedule.events[0], Event)
    assert schedule.events[0].note == "Stage 2"


def test_pick_auto_enabled_loadshedding() -> None:
    """Prefer auto_enabled loadshedding schedule."""
    area = CONVERTER.structure(AREA_EXAMPLE, Area)
    assert pick_schedule_id(area) == "eskde-14"


def test_pick_schedule_fallback() -> None:
    """Fall back to first schedule when none auto-enabled."""
    area = Area(
        id="x",
        name="Test",
        schedules=[
            ScheduleRef(id="sched-a", type="loadshedding"),
            ScheduleRef(id="sched-b", type="load_reduction", auto_enabled=True),
        ],
    )
    assert pick_schedule_id(area) == "sched-b"


def test_v2_schedule_id() -> None:
    """Map v2 hyphenated area id to schedule id."""
    assert v2_schedule_id("jhbcitypower3-2-victorypark") == "jhbcitypower3-2"
    assert v2_schedule_id("eskde-10-fourways") == "eskde-10"
