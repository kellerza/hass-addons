"""Bridge."""

from __future__ import annotations

import logging
import time
from typing import Any

import attrs
from mqtt_entity.client import MQTTClient
from mqtt_entity.device import MQTTDevice
from mqtt_entity.entities import (
    MQTTBaseEntity,
    MQTTDeviceTrigger,
    MQTTLightEntity,
    MQTTSwitchEntity,
)

from ..qsusb import QsWrite
from ..qwikswitch import parse_id, qs_encode, string_id
from .options import OPT, ButtonOpt, DeviceOpt

_LOGGER = logging.getLogger(__name__)


@attrs.define()
class HassBridge:
    """Bridge for Home Assistant integration."""

    qs_write: QsWrite
    devs: list[MQTTDevice] = attrs.field(factory=list)
    bridges: list[Bridge] = attrs.field(factory=list)
    client: MQTTClient = attrs.field(init=False, repr=False)

    async def mqtt_connect(self) -> None:
        """Connect to the MQTT broker and publish discovery info."""
        self.client = MQTTClient(
            devs=self.devs,
            availability_topic=f"{OPT.prefix}/status",
            origin_name="qsusb64",
            origin_version="1.0.0",
        )
        await self.client.connect(OPT)
        self.client.monitor_homeassistant_status()

    def find_id(self, qid: str) -> tuple[MQTTBaseEntity, Bridge]:
        """Find the entity by ID."""
        for ent in self.bridges:
            if base := ent.getid(qid):
                return base, ent
        raise ValueError(f"Entity with ID {qid} not found.")

    def __attrs_post_init__(self) -> None:
        """Create entities for the devices."""
        for opt in OPT.buttons:
            print(f"Creating button {opt.name}")
            br = ButtonBridge(
                opt=opt,
                dev=MQTTDevice(
                    name=f"{opt.name} buttons",
                    identifiers=sorted(qsslug(i) for i in opt.btn_map),
                    manufacturer="QwikSwitch",
                    model=opt.model or "",
                    components={},
                ),
            )
            br.create_entities(qs_write=self.qs_write)
            self.bridges.append(br)
            self.devs.append(br.dev)

        dev = MQTTDevice(
            name="QwikSwitch",
            identifiers=["qsusb64"],
            manufacturer="QwikSwitch",
            model="QwikSwitch USB Modem",
            components={},
        )
        self.devs.append(dev)
        for lig in OPT.lights:
            print(f"Creating light {lig.name}")
            ligb = LightBridge(opt=lig, dev=dev)
            self.bridges.append(ligb)
            ligb.create_entities(qs_write=self.qs_write)

        for swo in OPT.switches:
            print(f"Creating light {swo.name}")
            swb = LightBridge(opt=swo, dev=dev, switch=True)
            self.bridges.append(swb)
            swb.create_entities(qs_write=self.qs_write)


@attrs.define()
class Bridge:
    """Bridge class to handle communication between MQTT and the QS device."""

    dev: MQTTDevice

    def create_entities(self, qs_write: QsWrite) -> dict[str, MQTTBaseEntity]:
        """Return a generator of Home Assistant entities."""
        raise NotImplementedError("process_msg must be implemented in subclasses")

    async def process_msg(self, msg: dict[str, Any], client: MQTTClient) -> bool:
        """Process a message from the QS device."""
        raise NotImplementedError("process_msg must be implemented in subclasses")

    def getid(self, qid: str) -> MQTTBaseEntity | None:
        """Get the entity by ID."""
        raise NotImplementedError("getid must be implemented in subclasses")


@attrs.define()
class ButtonBridge(Bridge):
    """Bridge for button actions."""

    opt: ButtonOpt
    hassbtn: dict[str, MQTTDeviceTrigger] = attrs.field(init=False)
    press_time: float = attrs.field(default=0.0, init=False)

    def getid(self, qid: str) -> MQTTDeviceTrigger | None:
        """Get the entity by ID."""
        return self.hassbtn.get(qsslug(qid))

    def create_entities(self, qs_write: QsWrite) -> dict[str, MQTTBaseEntity]:
        """Return a generator of Home Assistant entities for the buttons."""
        self.hassbtn = dict[str, MQTTDeviceTrigger]()
        for btn_id, btn_type in self.opt.btn_map.items():
            _LOGGER.debug("Creating button entity %s -> %s", btn_id, btn_type)
            slug_id = qsslug(btn_id)
            self.hassbtn[slug_id] = MQTTDeviceTrigger(
                topic=f"{OPT.prefix}/{slug_id}_trigger",
                type="button_short_press",
                subtype=btn_type,
                payload="press",
            )
        self.dev.components.update(self.hassbtn)
        return dict(self.hassbtn)

    async def process_msg(self, msg: dict[str, Any], client: MQTTClient) -> bool:
        """Process a button message."""
        qid = msg.get("id")
        if not qid:
            return False

        # debounce 200ms
        if time.time() < self.press_time:
            return False
        self.press_time = time.time() + 0.2

        slug_id = qsslug(qid)
        if btn := self.hassbtn.get(slug_id):
            await btn.send_trigger(client)
            return True
        _LOGGER.warning("Button with ID %s not found in hassbtn", slug_id)
        return False


@attrs.define()
class LightBridge(Bridge):
    """Bridge for switch actions."""

    opt: DeviceOpt
    hassdev: MQTTLightEntity | MQTTSwitchEntity = attrs.field(init=False)
    switch: bool = attrs.field(default=False)

    def getid(self, qid: str) -> MQTTLightEntity | MQTTSwitchEntity | None:
        """Get the entity by ID."""
        if qid == self.opt.id:
            return self.hassdev
        return None

    def create_entities(self, qs_write: QsWrite) -> dict[str, MQTTBaseEntity]:
        """Create Home Assistant switch entities."""
        oid = string_id(parse_id(self.opt.id))
        slug_id = qsslug(oid)
        print(f"Creating device {self.opt} object_id={oid}")

        async def _cb(payload: str, topic: str) -> None:
            """Brightness change callback."""
            val = 0 if payload == "OFF" else 100 if payload == "ON" else payload
            try:
                val = int(val)
            except ValueError:
                val = 100

            if topic.endswith("/cmd"):
                _LOGGER.info("Command callback: %s", payload)
                qs_write(qs_encode("SET", self.opt.id, val))
            elif topic.endswith("/brightness_cmd"):
                _LOGGER.debug("Brightness change callback: %s", payload)
                qs_write(qs_encode("SET", self.opt.id, val))
            else:
                _LOGGER.warning("Unknown command topic: %s", topic)

        if self.switch:
            self.opt.kind = "rel"

        Kind = MQTTSwitchEntity if self.switch else MQTTLightEntity

        self.dev.components[slug_id] = self.hassdev = Kind(
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
            value = 0
            try:
                value = int(msg.get("val", 0))
            except ValueError:
                _LOGGER.error("Invalid brightness value: %s", msg.get("val"))
            await self.hassdev.send_brightness(client, brightness=value)
            return True

        return False


def qsslug(value: str) -> str:
    """Convert a string to a slug suitable for MQTT topics and ids."""
    return value.strip(" _").lower().replace("@", "qs_").replace(" ", "_")
