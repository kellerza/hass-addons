"""Base class for Home Assistant API wrappers."""

from __future__ import annotations

import logging
from functools import partialmethod
from typing import Any, Self

import attrs
from aiohttp import ClientSession
from mqtt_entity.supervisor import token

_LOG = logging.getLogger(__name__)


@attrs.define()
class LogBase:
    """Base class for logging."""

    _log_prefix = "LOG1: "
    log_debug_level: int = attrs.field(default=1, repr=False)

    def log_debugl(self, level: int, msg: str, *args: Any) -> None:
        """Log a debug message."""
        if level <= self.log_debug_level:
            _LOG.debug(self._log_prefix + msg, *args)

    log_debug = partialmethod(log_debugl, 1)
    log_debug2 = partialmethod(log_debugl, 1)
    log_debug3 = partialmethod(log_debugl, 3)

    def log_fstring(self, level: int, msg: str) -> None:
        """Log a formatted string message."""
        _LOG.log(level, self._log_prefix + msg)

    log_warn = partialmethod(log_fstring, logging.WARNING)
    log_error = partialmethod(log_fstring, logging.ERROR)
    log_info = partialmethod(log_fstring, logging.INFO)


@attrs.define()
class HaApiBase(LogBase):
    """Home Assistant API wrapper."""

    url: str = attrs.field(
        default="http://supervisor/core/",
        on_setattr=lambda _, __, v: (v or "http://supervisor/core/").strip("/") + "/",
    )
    token: str = attrs.field(
        factory=lambda: token(warn=False) or "",
        on_setattr=lambda _, __, v: str(v or token(warn=True)),
    )
    ses: ClientSession = attrs.field(factory=ClientSession)

    def set_from_options(self, opt: object) -> Self:
        """Set options from the given object."""
        self.log_debug_level = opt.debug  # type: ignore[attr-defined]
        self.url = opt.ha_api_url  # type: ignore[attr-defined]
        self.token = opt.ha_api_token  # type: ignore[attr-defined]
        return self

    async def close(self) -> None:
        """Close the API session."""
        if self.ses:
            await self.ses.close()
