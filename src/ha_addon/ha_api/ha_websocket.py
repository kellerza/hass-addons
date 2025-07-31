"""Home Assistant Websocket API helper.

https://developers.home-assistant.io/docs/api/websocket

You need `homeassistant_api: true` in config.yaml to access the Home Assistant API.
(http://supervisor/core/api & http://supervisor/core/websocket)

See https://developers.home-assistant.io/docs/add-ons/communication
"""

from __future__ import annotations

import asyncio
import inspect
import json
from collections.abc import Callable, Coroutine
from typing import Any, cast
from urllib.parse import urljoin

import attrs
from aiohttp import ClientWebSocketResponse, WSMsgType
from typing_extensions import TypeIs

from .base import HaApiBase

type MsgCallback = Callable[[dict[str, Any]], Coroutine[None, None, None]]

type StrCallback = Callable[[str], Coroutine[None, None, None]] | Callable[[str], None]

type StrOrMsgCallback = (
    StrCallback
    | Callable[[str, dict[str, Any]], Coroutine[None, None, None]]
    | Callable[[str, dict[str, Any]], None]
)


@attrs.define()
class HaWebsocketApi(HaApiBase):
    """Home Assistant Websocket API wrapper."""

    _ws: ClientWebSocketResponse = attrs.field(init=False, default=None)
    _ws_id: int = -1  # no auth
    running_tasks: list[asyncio.Task] = attrs.field(
        factory=list, init=False, repr=False
    )
    ws_msg_handlers: dict[str, MsgCallback] = attrs.field(
        factory=dict, init=False, repr=False
    )
    ws_event_handlers: dict[int, MsgCallback] = attrs.field(
        factory=dict, init=False, repr=False
    )
    _log_prefix = "HA WS: "
    _ha_authenticated: asyncio.Event = attrs.field(
        factory=asyncio.Event, init=False, repr=False
    )

    def __attrs_post_init__(self) -> Any:
        """Post initialization."""
        self.ws_msg_handlers.update(
            {
                "event": self.handle_event,
                "auth_required": self.handle_auth_required,
                "auth_ok": self.handle_auth_ok,
                "auth_invalid": self.handle_auth_invalid,
                "result": self.handle_result,
            }
        )

    def async_start_ws_loop(self) -> None:
        """Start the websocket API."""
        if self.connected:
            raise RuntimeError("Websocket already started")
        self.running_tasks.clear()
        self.running_tasks.append(asyncio.create_task(self.ws_loop()))

    async def close(self) -> None:
        """Close the API session."""
        for task in self.running_tasks:
            task.cancel()
        self.ws_event_handlers.clear()
        self._ha_authenticated.clear()
        self.running_tasks.clear()
        await asyncio.sleep(0.1)  # Allow pending messages to be processed
        await self.ses.close()

    @property
    def connected(self) -> bool:
        """Check if the websocket is connected."""
        return bool(self._ws) and bool(self.running_tasks) and self._ws_id >= 0

    async def wait_authenticated(self, wait_timeout: float = 10) -> bool:
        """Wait until the websocket is authenticated."""
        await asyncio.wait_for(self._ha_authenticated.wait(), wait_timeout)
        return self.connected

    async def send(
        self,
        message_as_dict: dict[str, Any] | None = None,
        /,
        result_callback: MsgCallback | None = None,
        **msg: Any,
    ) -> int | None:
        """Send a message to the websocket."""
        if message_as_dict:
            msg.update(message_as_dict)
        if not self.connected:
            self.log_warn("Websocket is not connected %s", msg)
            return None
        if "id" not in msg:
            self._ws_id += 1
            msg["id"] = self._ws_id
        data = json.dumps(msg)
        self.log_debug3("Sending websocket message: %s", data)
        if result_callback:
            self.ws_event_handlers[msg["id"]] = result_callback
        await self._ws.send_str(data)
        return msg.get("id")

    async def handle_auth_required(self, msg: dict[str, Any]) -> None:
        """Handle authentication messages."""
        await self._ws.send_json({"type": "auth", "access_token": self.token})

    async def handle_auth_invalid(self, msg: dict[str, Any]) -> None:
        """Handle invalid authentication messages."""
        self.log_error("Websocket authentication failed. Closing connection.")
        await self.close()

    async def handle_auth_ok(self, msg: dict[str, Any]) -> None:
        """Handle successful authentication messages."""
        self.log_info(
            f"Websocket authentication successful [version {msg.get('ha_version')}]"
        )
        self._ws_id = 0  # auth_ok
        self._ha_authenticated.set()

    async def handle_event(self, msg: dict[str, Any]) -> None:
        """Receive messages from the websocket."""
        m_id = cast(int, msg.get("id"))
        if not isinstance(m_id, int):
            self.log_error(f"Expect integer id, got {m_id}: {msg}")

        if handler := self.ws_event_handlers.get(m_id):
            handler = self.ws_event_handlers[m_id]
            event = msg.get("event", {"no-result?": msg})
            self.log_debug2(
                "Running handler %s for id %s: %s", handler.__name__, m_id, event
            )
            await self.ws_event_handlers[m_id](event)
        else:
            self.log_warn(f"Unhandled websocket event id {m_id}: {msg}")

    async def handle_result(self, msg: dict[str, Any]) -> None:
        """Handle result messages.

        HA-API: Unhandled websocket message type: result {'id': 4, 'type': 'result', 'success': True, 'result': None}
        """
        if not msg.get("success", False):
            self.log_error(f"Error in websocket message: {msg}")

    async def ws_loop(self) -> None:
        """Connect to Websocket.

        Create as a task.
        """
        url = (
            urljoin(self.url, "api/websocket")
            .replace("https", "ws")
            .replace("http", "ws")
        )
        self.log_info(f"Connecting to websocket: {url}")
        self._ws_id = -1  # no auth
        async with self.ses.ws_connect(url) as __ws:
            self._ws = __ws
            self.log_debug("connected")
            try:
                async for msg in self._ws:
                    if not self.running_tasks:
                        self.log_info("connection closed (running_tasks)")
                        return
                    if msg.type in (WSMsgType.ERROR,):
                        self.log_error("connection closed (ERROR)")
                        return
                    elif msg.type != WSMsgType.TEXT:
                        self.log_warn(
                            f"Received message of unknown type: {msg.type} {msg.data}"
                        )

                    data = json.loads(msg.data)

                    m_type = cast(str, data.get("type", ""))
                    if handler := self.ws_msg_handlers.get(m_type):
                        self.log_debug3(
                            "Running handler %s for type %s: %s",
                            handler.__name__,
                            m_type,
                            data,
                        )
                        await handler(data)
                    else:
                        self.log_warn(f"Unhandled message type: {m_type} {data}")
            except Exception as e:
                self.log_error(f"Error handling websocket messages: {e}")
            finally:
                await self.close()
            self.log_warn("Websocket connection closed")

    def ping(self, count: int = -1, interval: int = 10) -> None:
        """Ping websocket."""
        if self.ws_msg_handlers.get("pong"):
            raise RuntimeError("Ping already in progress")
        if not self.connected:
            self.log_warn("Websocket is not connected, cannot ping")
            return

        async def _pong(msg: dict[str, Any]) -> None:
            self.log_debug("Received pong message %s", msg)

        self.ws_msg_handlers["pong"] = _pong

        async def ping_loop(count: int, interval: int) -> None:
            try:
                await self.send(type="ping")
                while True:
                    if count > 0:
                        count -= 1
                        if count == 0:
                            break
                    await asyncio.sleep(interval)
                    if not self.connected:
                        break
                    await self.send(type="ping")
            except Exception as e:
                self.log_error(f"Error sending ping: {e}")
            finally:
                self.ws_msg_handlers.pop("pong", None)

        self.running_tasks.append(
            asyncio.create_task(ping_loop(count=count, interval=interval))
        )

    async def call_service(
        self,
        domain_service: str,
        service_data: dict[str, Any] | None = None,
        target_entity_ids: list[str] | None = None,
        return_response: bool = False,
    ) -> None:
        """Call a service.

        This will call a service action in Home Assistant. Right now there is no return value.
        The client can listen to state_changed events if it is interested in changed entities as a result of a call.

        return_response: Must be included for service actions that return response data.
        """
        domain, _, service = domain_service.partition(".")
        msg: dict[str, Any] = {
            "type": "call_service",
            "domain": domain,
            "service": service,
        }
        if service_data is not None:
            msg["service_data"] = service_data
        if target_entity_ids is not None:
            msg["target_entity_ids"] = target_entity_ids
        if return_response:
            msg["return_response"] = return_response
        await self.send(msg)

    async def render_template(
        self,
        template: str,
        result_callback: StrOrMsgCallback,
        report_errors: bool = True,
    ) -> int | None:
        """Render a template."""

        async def _cb(msg: dict[str, Any]) -> None:
            """Handle the result of the template rendering."""
            self.log_debug3(
                "Template rendered, calling callback %s: %s",
                result_callback.__name__,
                msg,
            )

            if err_msg := msg.get("error"):
                self.log_error(
                    f"Template rendering {msg.get('level', 'ERR')}: {err_msg}"
                )

            result = str(msg.get("result", ""))
            param = [msg]
            if isStrCallback(result_callback):
                param = []

            if asyncio.iscoroutinefunction(result_callback):
                await result_callback(result, *param)
            else:
                result_callback(result, *param)

        res = await self.send(
            type="render_template",
            template=template,
            report_errors=report_errors,
            result_callback=_cb,
        )
        return res

    async def subscribe_events(
        self, event_type: str | None, callback: MsgCallback
    ) -> int | None:
        """Subscribe to websocket events."""
        msg = {"event_type": event_type} if event_type is not None else {}
        return await self.send(msg, type="subscribe_events", callback=callback)

    async def subscribe_triggers(
        self, trigger: dict[str, Any], callback: MsgCallback
    ) -> int | None:
        """Subscribe to websocket triggers."""
        return await self.send(
            type="subscribe_trigger", trigger=trigger, callback=callback
        )

    async def unsubscribe_events(self, event_id: int) -> None:
        """Unsubscribe from websocket events."""
        await self.send(type="unsubscribe_events", event_id=event_id)


def isStrCallback(
    callback: MsgCallback | StrOrMsgCallback,
) -> TypeIs[StrCallback]:
    """Check if the callback is a StrCallback."""
    params = list(inspect.signature(callback).parameters.values())
    return len(params) == 1
    # return params[0].annotation is str
