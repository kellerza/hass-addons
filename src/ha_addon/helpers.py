"""Helpers."""

import logging

_LOG = logging.getLogger(__name__)


def onoff(state: str | bool | int | None) -> str:
    """Convert state to on/off."""
    if state is None:
        return "off"
    if isinstance(state, bool):
        return "on" if state else "off"
    if isinstance(state, int):
        return "off" if state == 0 else "on"

    ss = state.strip()
    if ss in ("0", "off"):
        return "off"
    elif ss in ("1", "on", "100"):
        return "on"
    _LOG.warning("Unknown state %s, defaulting to off", state)
    return "off"
