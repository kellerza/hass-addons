"""Home Assistant REST API & Websocket helper.

https://developers.home-assistant.io/docs/api/rest
https://developers.home-assistant.io/docs/api/websocket

You need `homeassistant_api: true` in config.yaml to access the Home Assistant API.
(http://supervisor/core/api & http://supervisor/core/websocket)

See https://developers.home-assistant.io/docs/add-ons/communication
"""

from .base import HaApiBase, LogBase
from .ha_rest import HaRestApi
from .ha_websocket import HaWebsocketApi

__all__ = [
    "HaApiBase",
    "HaRestApi",
    "HaWebsocketApi",
    "LogBase",
]
