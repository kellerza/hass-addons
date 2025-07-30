"""Control group add-on."""

import asyncio
import logging
import sys

import attrs
from mqtt_entity import MQTTClient, MQTTDevice, MQTTSensorEntity

from ha_addon.all_apis import HaAllApis
from ha_addon.helpers import onoff

from .options import ControlGroupOptions, Options

_LOG = logging.getLogger(__name__)

TEM1 = "{{ states('sun.sun') }}"


API = HaAllApis[Options]()
ACHANGE = asyncio.Event()


async def main_loop() -> int:
    """Entry point."""
    opt = API.opt = Options()
    await opt.init_addon()

    await API.connect_rest_ws()

    tmpl = API.opt.groups[4].template
    res = await API.rest.render_template(tmpl)
    _LOG.info("RESTAPI Rendered template %s", res)

    dev = MQTTDevice(
        name="Control group",
        identifiers=[opt.uuid],
        components={},
    )
    mqtt = API.mqtt = MQTTClient(
        availability_topic="cgroup/availability",
        devs=[dev],
        origin_name="Control Group add-on",
    )

    # dev.components["ts"] = texte = MQTTTextEntity(
    #     "Template states",
    #     unique_id=dev.id + "_ts",
    #     object_id=f"{opt.ha_prefix}_debug_edit",
    #     state_topic="cgroup/template_states",
    #     command_topic="cgroup/template_states_set",
    #     on_command=lambda msg: _LOG.info("Received command: %s", msg),
    # )
    mqtt.devs[0].remove_components["ts"] = "text"
    texte = dev.components["dbg"] = MQTTSensorEntity(
        "Template states",
        unique_id=dev.id + "_dbg",
        object_id=f"{opt.ha_prefix}_debug",
        state_topic="cgroup/template_states",
        entity_category="diagnostic",
    )

    await mqtt.connect(opt)
    mqtt.monitor_homeassistant_status()

    # wait a bit for discovery
    await asyncio.sleep(10)

    cgs = [CGroupBridge(opt=g) for g in opt.groups]

    async def websocket_connected() -> None:
        """Render template on websocket. Have to repeat after a disconnect."""
        for cg in cgs:
            await API.ws.render_template(cg.opt.template, cg.template_rendered)

    await websocket_connected()
    texte_state = ""

    try:
        while True:
            try:
                await asyncio.sleep(0.2)
                if not API.ws.connected:
                    await asyncio.sleep(2)
                    _LOG.info("Websocket not connected, reconnecting...")
                    await API.connect_rest_ws()
                    await websocket_connected()

                if ACHANGE.is_set():
                    ACHANGE.clear()
                    tgtg_text = "- " + "\n- ".join(
                        f"{g.opt.entities[0]}={g.state} {g.state_reason}".strip()
                        for g in cgs
                    )
                    if tgtg_text != texte_state:
                        texte_state = tgtg_text
                        await texte.send_state(mqtt, texte_state)

            except asyncio.CancelledError:
                _LOG.info("Shutting down cgroup sensors")
                break
            except Exception as ex:
                _LOG.error("Error in main loop: %s", ex, exc_info=True)
    finally:
        await API.close()

    return 0


@attrs.define()
class CGroupBridge:
    """Control group bridge."""

    opt: ControlGroupOptions
    state_reason: str = ""
    state: str = ""

    async def template_rendered(self, msg: str) -> None:
        """Handle template rendered callback."""
        self.state, _, self.state_reason = msg.strip().partition(",")
        self.state = onoff(self.state)
        states = [await API.rest.get_state(e) for e in self.opt.entities]
        diff = [s for s in states if s and s.state != self.state]
        if diff:
            _LOG.info(
                "Cgroup set state %s=%s",
                ",".join(s.entity_id for s in diff),
                self.state,
            )
            self.state_reason += f" [will update {' '.join(s.entity_id for s in diff)}]"
        ACHANGE.set()
        for st in diff:
            await API.rest.set_entity_state(st.entity_id, self.state)

    async def render_cgroup_rest(self) -> None:
        """Check if cgroup is ok."""
        template = await API.rest.render_template(self.opt.template)
        if not template:
            self.state_reason = "Template rendering failed"
            return
        await self.template_rendered(template)


if __name__ == "__main__":
    sys.exit(asyncio.run(main_loop()))
