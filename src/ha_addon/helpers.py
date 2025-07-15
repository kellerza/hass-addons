"""Home Assistant Addon Helpers."""

import logging
import os
from pathlib import Path

import colorlog
from aiohttp import ClientSession
from mqtt_entity.options import MQTTOptions

_LOGGER = logging.getLogger(__name__)


def ha_share_path(addon_slug: str, create: bool = False) -> Path:
    """Get the root folder for data and mysensors."""
    root = (
        Path(f"/share/{addon_slug}/")
        if os.name != "nt"
        else Path(__name__).parent.parent / ".data"
    )
    if create and not root.exists():
        root.mkdir(parents=True)
    return root


def slug(name: str) -> str:
    """Create a slug."""
    return name.lower().replace(" ", "_").replace("-", "_")


MQFAIL = "MQTT: Failed to get MQTT service details from the Supervisor"


async def get_mqtt_details(opt: MQTTOptions) -> None:
    """Get MQTT details from Home Assistant Supervisor."""
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        _LOGGER.log(
            logging.DEBUG if opt.mqtt_password else logging.WARNING,
            "%s - no SUPERVISOR_TOKEN",
            MQFAIL,
        )
        return
    head = {"Authorization": f"Bearer {token}", "content-type": "application/json"}
    async with ClientSession() as session:
        async with session.get("http://supervisor/services/mqtt", headers=head) as res:
            if res.status != 200:
                _LOGGER.warning("%s - response %s", MQFAIL, res.status)
                return
            data = await res.json()
            try:
                data = data["data"]
                opt.mqtt_host = data["host"]
                opt.mqtt_port = data["port"]
                opt.mqtt_username = data["username"]
                opt.mqtt_password = data["password"]
            except KeyError as err:
                _LOGGER.warning("%s: %s %s", MQFAIL, err, data)


def logging_color() -> None:
    """Enable color logging."""
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "[%(asctime)s] %(log_color)s%(levelname)s%(reset)s %(message)s",
            datefmt="%H:%M:%S",
            reset=False,
        )
    )
    logging.basicConfig(
        # format="[%(asctime)s] %(levelname)-7s %(message)s",
        level=logging.INFO,
        handlers=[handler],
        force=True,
    )
