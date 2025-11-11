"""Bridge."""

from __future__ import annotations

import logging
from typing import Any

import attrs
from mqtt_entity.client import MQTTClient
from mqtt_entity.device import MQTTDevice
from mqtt_entity.entities import (
    MQTTBaseEntity,
    MQTTBinarySensorEntity,
    MQTTLightEntity,
    MQTTSensorEntity,
    MQTTSwitchEntity,
)
from mqtt_entity.utils import tostr

from ..qsusb import QsWrite
from ..qwikswitch import qs_encode, qsslug
from .options import OPT, DeviceOpt

_LOG = logging.getLogger(__name__)


@attrs.define()
class Bridge:
    """Bridge class to handle communication between MQTT and the QS device."""

    dev: MQTTDevice

    def create_entities(self, qs_write: QsWrite) -> dict[str, MQTTBaseEntity]:
        """Return a generator of Home Assistant entities."""
        raise NotImplementedError()

    async def process_msg(self, msg: dict[str, Any], client: MQTTClient) -> bool:
        """Process a message from the QS device."""
        raise NotImplementedError()

    def find_entity(self, qid: str) -> MQTTBaseEntity | None:
        """Get the entity by ID."""
        raise NotImplementedError()


@attrs.define()
class Bridge1(Bridge):
    """Bridge for sensor actions."""

    opt: DeviceOpt

    platform = "#"
    slug_post = "#"

    def find_entity(self, qid: str) -> MQTTBaseEntity | None:
        """Get the entity by ID."""
        if qid == self.opt.id:
            return getattr(self, "hassdev", None)
        return None

    @property
    def uid(self) -> str:
        """Get the HA unique ID."""
        return qsslug(self.opt.id, parse=True) + self.slug_post


@attrs.define()
class LightBridge(Bridge1):
    """Bridge for switch actions."""

    opt: DeviceOpt
    hassdev: MQTTLightEntity | MQTTSwitchEntity = attrs.field(init=False)

    platform = "light"
    slug_post = "_l"

    def create_entities(self, qs_write: QsWrite) -> dict[str, MQTTBaseEntity]:
        """Create Home Assistant switch entities."""
        slug_id = self.uid
        print(f"Creating device {self.opt} unique_id={slug_id}")

        async def _cb(payload: str, topic: str) -> None:
            """Brightness change callback."""
            val = 0 if payload == "OFF" else 100 if payload == "ON" else payload
            try:
                val = int(val)
            except ValueError:
                val = 100

            if topic.endswith("/cmd"):
                _LOG.info("Command callback: %s", payload)
                qs_write(qs_encode("SET", self.opt.id, val))
            elif topic.endswith("/brightness_cmd"):
                _LOG.debug("Brightness change callback: %s", payload)
                qs_write(qs_encode("SET", self.opt.id, val))
            else:
                _LOG.warning("Unknown command topic: %s", topic)

        is_switch = isinstance(self, SwitchBridge)
        dev_class = MQTTSwitchEntity if is_switch else MQTTLightEntity

        self.dev.components[slug_id] = self.hassdev = dev_class(
            unique_id=slug_id,
            state_topic=f"{OPT.prefix}/{slug_id}/state",
            name=self.opt.name,
            command_topic=f"{OPT.prefix}/{slug_id}/cmd",
            on_command=_cb,
        )
        if self.opt.kind == "dim" and isinstance(self.hassdev, MQTTLightEntity):
            self.hassdev.brightness_command_topic = (
                f"{OPT.prefix}/{slug_id}/brightness_cmd"
            )
            self.hassdev.on_brightness_change = _cb
            self.hassdev.brightness_state_topic = (
                f"{OPT.prefix}/{slug_id}/brightness_state"
            )
        return {slug_id: self.hassdev}

    async def process_msg(self, msg: dict[str, Any], client: MQTTClient) -> bool:
        """Process a switch message."""
        qid = msg.get("id")
        if not qid or qid != self.opt.id:
            return False

        if self.opt.kind == "rel" or isinstance(self.hassdev, MQTTSwitchEntity):
            await self.hassdev.send_state(client, payload=str(msg.get("val")))
            return True

        if self.opt.kind == "dim":
            value = bright2val(msg.get("val"))
            await self.hassdev.send_brightness(client, brightness=value)
            await self.hassdev.send_state(client, payload=bool(value))
            return True

        if self.opt.kind == "imod":
            value = bright2val(msg.get("val"))
            await self.hassdev.send_state(client, payload=bool(value))
            return True

        return False


def bright2val(bright: Any) -> int:
    """Convert brightness to value."""
    if bright:
        try:
            if isinstance(bright, str):
                if bright.endswith("%"):
                    return round(int(bright.strip("%")) * 255 / 100)
                elif bright == "ON":
                    return 255
                elif bright == "OFF":
                    return 0
            return int(bright)
        except ValueError:
            _LOG.error("Invalid brightness value: %s", bright)
    return 0


@attrs.define()
class SwitchBridge(LightBridge):
    """Bridge for switch actions."""

    platform = "switch"
    slug_post = "_sw"


@attrs.define()
class BinarySensorBridge(Bridge1):
    """Binary Sensor Bridge."""

    hassdev: MQTTBinarySensorEntity = attrs.field(init=False)
    toggle: bool = False

    platform = "binary_sensor"
    slug_post = "_bs"

    def create_entities(self, qs_write: QsWrite) -> dict[str, MQTTBaseEntity]:
        """Create Home Assistant switch entities."""
        slug_id = self.uid
        print(f"Creating device {self.opt} unique_id={slug_id}")

        self.dev.components[slug_id] = self.hassdev = MQTTBinarySensorEntity(
            name=self.opt.name,
            unique_id=slug_id,
            state_topic=f"{OPT.prefix}/{slug_id}/state",
        )
        return {slug_id: self.hassdev}

    async def process_msg(self, msg: dict[str, Any], client: MQTTClient) -> bool:
        """Process a switch message."""
        m_id = msg.get("id")
        if not m_id or m_id != self.opt.id:
            return False

        m_val = msg.get("val")
        if m_val is None:
            m_val = self.toggle = not self.toggle

        await self.hassdev.send_state(client, payload=tostr(bool(m_val)))
        return True


@attrs.define()
class SensorBridge(Bridge1):
    """Sensor Bridge, incrementing count."""

    hassdev: MQTTSensorEntity = attrs.field(init=False)

    count: int = attrs.field(default=0)
    platform = "sensor"
    slug_post = "_s"

    def create_entities(self, qs_write: QsWrite) -> dict[str, MQTTBaseEntity]:
        """Create Home Assistant switch entities."""
        self.dev.components[self.uid] = self.hassdev = MQTTSensorEntity(
            name=self.opt.name,
            unique_id=self.uid,
            state_topic=f"{OPT.prefix}/{self.uid}/state",
        )
        return {self.uid: self.hassdev}

    async def process_msg(self, msg: dict[str, Any], client: MQTTClient) -> bool:
        """Process a switch message."""
        m_id = msg.get("id")
        if not m_id or m_id != self.opt.id:
            return False
        self.count += 1
        await self.hassdev.send_state(client, payload=self.count)
        return True
