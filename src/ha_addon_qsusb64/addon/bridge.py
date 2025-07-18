"""Bridge."""

from __future__ import annotations

import logging
import time
from collections.abc import Generator
from typing import Any

import attrs
from mqtt_entity.client import MQTTClient
from mqtt_entity.device import MQTTDevice
from mqtt_entity.entities import (
    MQTTBaseEntity,
    MQTTDeviceTrigger,
)

from ..qsusb import QsWrite
from .entity_bridge import (
    BinarySensorBridge,
    Bridge,
    Bridge1,
    LightBridge,
    SensorBridge,
    SwitchBridge,
    qsslug,
)
from .options import OPT, ButtonOpt

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

    def find_ids(
        self, qid: str
    ) -> Generator[tuple[MQTTBaseEntity, Bridge], None, None]:
        """Find the entity by ID."""
        cnt = 0
        for ent in self.bridges:
            if base := ent.find_entity(qid):
                yield base, ent
                cnt += 1
        if cnt == 0:
            if qid not in [i.id for i in OPT.ignore]:
                _LOGGER.warning(f"ID not found {qid}")
            else:
                _LOGGER.debug(f"ID {qid} is in the ignore list.")

    def __attrs_post_init__(self) -> None:
        """Create entities for the devices."""
        # All entities will share the **QS device**
        dev = MQTTDevice(
            name="QwikSwitch",
            identifiers=["qsusb64"],
            manufacturer="QwikSwitch",
            model="QwikSwitch USB Modem",
            components={},
        )
        self.devs.append(dev)

        # Button **devices** will have a DeviceTrigger per button
        for btn in OPT.buttons:
            self.bridges.append(ButtonDevBridge.dev_factory(btn))
            self.devs.append(self.bridges[-1].dev)

        # Entity bridges
        self.bridges.extend([LightBridge(opt=opt, dev=dev) for opt in OPT.lights])
        self.bridges.extend([SwitchBridge(opt=opt, dev=dev) for opt in OPT.switches])
        self.bridges.extend(
            [BinarySensorBridge(opt=opt, dev=dev) for opt in OPT.binary_sensors]
        )
        self.bridges.extend([SensorBridge(opt=opt, dev=dev) for opt in OPT.sensors])

        # create all entities
        for bridge in self.bridges:
            bridge.create_entities(qs_write=self.qs_write)

        # Get all QS ids
        all_ids = [
            b.uid.rpartition("_")[0] for b in self.bridges if isinstance(b, Bridge1)
        ]
        for b in (b for b in self.bridges if isinstance(b, ButtonDevBridge)):
            all_ids.extend(b.hassbtn.keys())
        all_ids.extend(qsslug(i.id, parse=True) for i in OPT.ignore)

        _LOGGER.debug("All QS IDs: %s", all_ids)

        # remove other platforms
        for br in (
            LightBridge,
            SwitchBridge,
            BinarySensorBridge,
            SensorBridge,
        ):
            for uid_ in all_ids:
                uid = uid_ + br.slug_post
                if uid not in dev.components:
                    dev.remove_components[uid] = br.platform


@attrs.define()
class ButtonDevBridge(Bridge):
    """Bridge for button actions."""

    opt: ButtonOpt
    hassbtn: dict[str, MQTTDeviceTrigger] = attrs.field(init=False)
    press_time: float = attrs.field(default=0.0, init=False)

    @classmethod
    def dev_factory(cls, opt: ButtonOpt) -> ButtonDevBridge:
        """Create a button device bridge."""
        print(f"Creating button device {opt.name}")
        return ButtonDevBridge(
            opt=opt,
            dev=MQTTDevice(
                name=f"{opt.name} buttons",
                identifiers=sorted(qsslug(i) for i in opt.btn_map),
                manufacturer="QwikSwitch",
                model=opt.model or "",
                components={},
            ),
        )

    def find_entity(self, qid: str) -> MQTTDeviceTrigger | None:
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
