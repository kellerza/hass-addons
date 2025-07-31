"""Control group add-on."""

from __future__ import annotations

import asyncio
import logging
from ast import literal_eval

import attrs
from mqtt_entity import MQTTClient, MQTTDevice, MQTTSelectEntity, MQTTSensorEntity
from mqtt_entity.utils import slug

from ha_addon.helpers import onoff

from .options import API, ControlGroupOptions
from .options_file import OPT_FILE, FileGroupOption

_LOG = logging.getLogger(__name__)
ACHANGE = asyncio.Event()


@attrs.define()
class AddonState:
    """Main addon state."""

    cgs: list[CGroupBridge] = attrs.field(factory=list)

    dev: MQTTDevice = attrs.field(init=False)
    debug_sensor: MQTTSensorEntity = attrs.field(init=False)
    debug_sensor_state: str = ""

    async def connect_mqtt(self) -> None:
        """Init MQTT entities and connect."""
        self.dev = MQTTDevice(
            name=f"Control group {API.opt.name}",
            identifiers=[OPT_FILE.uuid],
            components={},
            manufacturer=" ",
            model=" ",
        )
        API.mqtt = MQTTClient(
            availability_topic=f"/cg/{API.opt.ha_prefix}_status",
            devs=[self.dev],
            origin_name=f"Control Group add-on {API.opt.name}",
        )

        debug_id = "debug"

        self.debug_sensor = self.dev.components[debug_id] = MQTTSensorEntity(
            f"Template states {API.opt.name}",
            unique_id=f"{self.dev.id}_{debug_id}",
            object_id=f"{API.opt.ha_prefix}_debug",
            state_topic=f"/cg/{API.opt.ha_prefix}/template_states",
            entity_category="diagnostic",
        )
        for cg in self.cgs:
            cg.register_mqtt(self.dev)

        await API.mqtt.connect(API.opt)
        API.mqtt.monitor_homeassistant_status()

        await API.mqtt.wait_connected()
        await asyncio.sleep(0.2)
        for cg in self.cgs:
            await cg.mode_entity.send_state(API.mqtt, cg.file_opt.mode)

    async def websocket_on_connect(self) -> None:
        """Render template on websocket.

        Repeat after a re-connect.
        """
        for cg in self.cgs:
            await cg.register_ws()

    async def run_loop(self) -> None:
        """Run the main loop."""
        if ACHANGE.is_set():
            ACHANGE.clear()
            tgtg_text = "- " + "\n- ".join(
                f"{','.join(g.opt.entities)}={g.state} {g.state_reason}".strip()
                for g in STATE.cgs
            )
            if tgtg_text != self.debug_sensor_state:
                self.debug_sensor_state = tgtg_text
                await self.debug_sensor.send_state(API.mqtt, self.debug_sensor_state)


STATE = AddonState()
MODE_OPTIONS = [
    "enabled",
    "disabled",
    "on",
    "off",
]


@attrs.define()
class CGroupBridge:
    """Control group bridge."""

    opt: ControlGroupOptions
    state_reason: str = ""
    state: str = ""
    mode_entity: MQTTSelectEntity = attrs.field(init=False)

    file_opt: FileGroupOption = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        """Post-initialization processing."""
        if opt := OPT_FILE.groups.get(self.opt.id):
            self.file_opt = opt
        else:
            self.file_opt = OPT_FILE.groups[self.opt.id] = FileGroupOption(
                mode=MODE_OPTIONS[0] if self.opt.template else MODE_OPTIONS[1]
            )

    @property
    def mode(self) -> str:
        """Get the mode of the control group."""
        return self.file_opt.mode

    @mode.setter
    def mode(self, value: str) -> None:
        """Set the mode of the control group."""
        if value not in self.mode_entity.options:
            _LOG.error(
                "Invalid mode value '%s' for control group '%s'",
                value,
                self.opt.id,
            )
        if value != self.file_opt.mode:
            self.file_opt.mode = value
            OPT_FILE.save_file()

    @property
    def kick_template(self) -> str:
        """The kick template ensures the listeners includes controlled entities."""
        states = "+".join(f"states('{e}')" for e in self.opt.entities)
        return "{%- set _kick=" + states + " -%}" if self.opt.entities else ""

    async def on_render(self, msg: str) -> None:
        """Handle template rendered callback."""
        if self.opt.call_script:
            # await API.ws.call_service(self.opt.call_script, {"msg": msg})
            await API.rest.call_service(self.opt.call_script, {"msg": msg})

        match self.mode:
            case "enabled":
                self.state, _, self.state_reason = msg.strip().partition(",")
                self.state = onoff(self.state)
            case "on":
                _, _, r = msg.strip().partition(",")
                self.state_reason = f"FORCED {r}"
                self.state = "on"
            case "off":
                _, _, r = msg.strip().partition(",")
                self.state_reason = f"FORCED {r}"
                self.state = "off"
            case "disabled":
                _, _, r = msg.strip().partition(",")
                self.state_reason = f"DISABLED {r}"
                return
            case _:
                _LOG.warning(
                    "Unknown mode value '%s' for control group '%s'",
                    self.mode,
                    self.opt.id,
                )
                return

        # sync the state
        current_state = [await API.rest.get_state(e) for e in self.opt.entities]
        diff = [s for s in current_state if s and s.state != self.state]
        if diff:
            ents = ",".join(s.entity_id for s in diff)
            _LOG.info("Cgroup set %s=%s", ents, self.state)
            self.state_reason += f" [will update {' '.join(s.entity_id for s in diff)}]"
        ACHANGE.set()

        # set the values
        for st in diff:
            await API.rest.set_entity_state(st.entity_id, self.state)

    async def render_template(self) -> None:
        """Render template with REST API."""
        template = await API.rest.render_template(self.opt.template)
        if template:
            return await self.on_render(template)
        self.state_reason = "Template rendering failed"

    async def register_ws(self) -> None:
        """Register the control group with the websocket."""
        await API.ws.render_template(
            self.kick_template + self.opt.template, self.on_render
        )

    async def expand_entities(self) -> None:
        """Expand entities in the control group."""
        for ent in list(self.opt.entities):
            if "{{" in ent and "}}" in ent:
                res = await API.rest.render_template(ent)
                self.opt.entities.remove(ent)
                try:
                    if res:
                        resl = literal_eval(res)
                        self.opt.entities.extend(resl)
                        _LOG.info("Expanding template '%s' \nto '%s'", ent, resl)
                except Exception as e:
                    _LOG.error("Error expanding template '%s': %s %s", ent, e, res)

    async def on_command_state(self, payload: str) -> None:
        """Handle state changes."""
        self.mode = payload.strip()
        await self.mode_entity.send_state(API.mqtt, payload)
        await self.render_template()

    def register_mqtt(self, mq_dev: MQTTDevice) -> None:
        """Register the control group with the MQTT broker."""
        name = self.opt.name or " ".join(self.opt.entities)

        async def _cb(msg: str) -> None:
            await self.on_command_state(msg)

        self.mode_entity = mq_dev.components[self.opt.id] = MQTTSelectEntity(
            name=f"{name} mode",
            unique_id=mq_dev.id + f"_{self.opt.id}",
            object_id=f"{API.opt.ha_prefix}_{slug(name)}_mode",
            options=MODE_OPTIONS,
            state_topic=f"/cg/{API.opt.ha_prefix}/{self.opt.id}",
            command_topic=f"/cg/{API.opt.ha_prefix}/{self.opt.id}_set",
            on_command=_cb,
        )
