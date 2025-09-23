"""Home Assistant API helper.

https://developers.home-assistant.io/docs/api/rest

You need `homeassistant_api: true` in config.yaml to access the Home Assistant API.
(http://supervisor/core/api & http://supervisor/core/websocket)

See https://developers.home-assistant.io/docs/add-ons/communication
"""

from __future__ import annotations

from typing import Any, TypeVar, get_origin
from urllib.parse import urljoin

import attrs
from colorama import Fore, Style
from mqtt_entity.options import CONVERTER

from .base import HaApiBase
from .types import HAEvents, HAService, HAState

T = TypeVar("T", default=dict[str, Any])


@attrs.define()
class HaRestApi(HaApiBase):
    """Home Assistant REST API wrapper."""

    _log_prefix = "HA REST: "

    def _head(self) -> dict[str, str]:
        """Return the headers for the HA API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        }

    async def render_template(self, template: str) -> str | None:
        """Render a template in Home Assistant - /api/template."""
        url = urljoin(self.url, "api/template")
        data = {"template": template}
        headers = self._head()
        self.log_debug("%s %s", url, data)
        async with self.ses.post(url, json=data, headers=headers) as res:
            if res.status == 200:
                return await res.text()
            msg = f"Failed to render template:\n{template}\n{Fore.RED}Error:{Fore.RESET}{Style.BRIGHT} "
            try:
                msg += f"\n{await res.text()} [{res.status}]"
            except Exception:
                msg += f" status={res.status}"
            msg += f"Template:\n{template}"
            self.log_error(msg)
            return None

    async def request(
        self,
        url: str,
        data: dict[str, Any] | None,
        *,
        method: str = "GET",
        return_type: type[T] | None = None,
    ) -> T | None:
        """Send a request."""
        url = urljoin(self.url, url)
        headers = self._head()
        self.log_debug("%s %s %s", method, url, data)
        async with self.ses.request(method, url, headers=headers, json=data) as res:
            if res.status == 200:
                if return_type is str or get_origin(return_type) is str:
                    return await res.text()  # type: ignore[return-value]
                return await res.json()
            msg = f"{method} {url} returned"
            try:
                msg += f" {await res.text()} [{res.status}]"
            except Exception:
                msg += f" status={res.status}"
            if data:
                msg += f" [data={data}]"
            self.log_error(msg)
            return None

    async def call_service(
        self, domain_service: str, data: dict[str, Any]
    ) -> list[HAState]:
        """Call a service - /api/services/<domain>/<service>."""
        res = await self.request(
            f"api/services/{domain_service.replace('.', '/')}", data=data, method="POST"
        )
        return CONVERTER.structure(res, list[HAState]) if res else []

    async def get_config(self) -> dict[str, Any] | None:
        """Get the Home Assistant configuration - /api/config."""
        res = await self.request("api/config", None)
        return res

    async def get_error_log(self) -> list[str]:
        """Get the Home Assistant error log - /api/error_log."""
        res = await self.request("api/error_log", None, return_type=str)
        return res.splitlines() if res else []

    async def get_events(self) -> list[HAEvents]:
        """Get the Home Assistant events - /api/events."""
        res = await self.request("api/events", None)
        return CONVERTER.structure(res, list[HAEvents]) if res else []

    async def get_services(self) -> list[HAService]:
        """Get the Home Assistant services - /api/services."""
        res = await self.request("api/services", None)
        return CONVERTER.structure(res, list[HAService]) if res else []

    async def get_state(self, entity_id: str) -> HAState | None:
        """Get the Home Assistant states - /api/states."""
        res = await self.request(f"api/states/{entity_id}", None)
        return CONVERTER.structure(res, HAState) if res else None

    async def get_states(self) -> list[HAState]:
        """Get the Home Assistant states - /api/states."""
        res = await self.request("api/states", None)
        return CONVERTER.structure(res, list[HAState]) if res else []

    async def is_running(self) -> bool:
        """Check if the API is available - /api."""
        res = await self.request("api/", None)
        return bool(res and res.get("message"))

    async def set_entity_state(self, entity_id: str, state: str) -> None:
        """Set the state of an entity - /api/states/<entity_id>."""
        domain, _, _ = entity_id.partition(".")
        if domain not in ("light", "switch"):
            self.log_warn(
                f"{domain} is not a valid domain for setting state. Use call_service instead.",
            )
            return
        self.log_debug("Setting state of %s to %s", entity_id, state)
        await self.call_service(
            f"{domain}.turn_on" if state == "on" else f"{domain}.turn_off",
            {"entity_id": entity_id},
        )
