# Control group add-on

The control group add-on allows you to control the state of entities (e.g. lights and switches),
based on the result of a template, or **template sensor** helper.

This allows you to easily build motion or presence-based automations using the state of other
entities:

- When did they last change (indicating movement for PIR, or binary_sensors)
- When a button was pressed
- The state of another switch, light or basically any entity's state or attribute.
- During the evening, when the sun sets, or based on a specific time of the day

The template can be as simple or as complex as you need it to be. You can add a reason to your
desired state, which makes it really easy to debug and fine-tune your automations.

Templates are standard Home Assistant
[templates](https://www.home-assistant.io/docs/configuration/templating/). The sections below shows
several examples.

## Alternative options

A similar concept can be achieved using a combination of existing Home Assistant features:

- You can use an automation or blueprint that syncs the value of this template sensor to the desired
  entity.

- Home Assistant has
  [Template Triggers](https://www.home-assistant.io/docs/automation/trigger/#template-trigger) that
  can be used for automations, but unfortunately only when the template state changes from False to
  True. For some discussions see [PR#121451](https://github.com/home-assistant/core/pull/121451).

## Installation

1. Add the *hass-addons* repository to your Home Assistant

   [![Open your Home Assistant instance and add the kellerza/hass-addons URL](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fkellerza%2Fhass-addons)

2. Install the addon, configure and run.

## Configuration

If you run on the HA OS, no configuration should be required. You can set the **NAME** of the
control group and the **PREFIX** that will be used for created entities.

and **HA_PREFIX** to your liking, but the default values should work fine. The addon will
automatically discover your Home Assistant instance and connect to it.

```yaml
NAME: main
HA_PREFIX: cgroup
```

All other parameters are optional and will be populated automaticlally when you run on HA OS by the
HA Supervisor.

> Example configuration for running the addon in a docker container:
>
> ```yaml
> HA_API_URL: http://192.168.1.8:8123
> HA_API_TOKEN: "***"
> MQTT_HOST: 192.168.1.8
> MQTT_PORT: 1883
> MQTT_USERNAME: hass
> MQTT_PASSWORD: password123
> ```
>
> The main task would be creating template helpers
>

## Template sensor helpers

A **Template sensor helper** can be created in the UI under *Devices & services* --> *Helpers*.

The template should return the state of the entity (on/off/0/1) and optionally a description,
separated by a comma. The description helps you to debug your templates and understand why a certain
entity is on or off.

The name of the **Template sensor helper** determines which entity will be controlled. If you take
the name of the template sensor helper and remove the *_state* suffix, you get the name of the
entity that will be controlled. For example, if you create a template sensor helper with the name
`sensor.porch_light_state`, the addon will search for entities without the *_state* suffix, i.e.
`light.porch_light` and `switch.porch_light`.

For a **Template sensor helper** to be considered, it needs to be labelled with **control group**.

The following table shows the naming convention:

| Template sensor helper   | Controlled entity | Mode selector            |
| ------------------------ | ----------------- | ------------------------ |
| sensor.porch_light_state | light.porch_light | select.porch_light_state |
| sensor.front_light_state | light.front_light | select.front_light_state |

The **Controlled entity** is the entity that will be switched on/off based on the template sensor
helper's state. The addon will automatically search for entities with the same name as the template
sensor helper, but without the *_state* suffix. It will also search for both light and switch
entities, so you can control either type of entity with the same template sensor helper.

The **Mode selector** is a select entity that allows you to override the template sensor helper's
mode of operation. It is automatically created by the addon. It has the following options:

- *Enabled*, the state of the controlled entity will be controlled by the template sensor helper.
- *Disabled*, the control group will be disabled and the state of the controlled entity will not be
  changed by the addon.
- *On* / *Off*, the state of the controlled entity will be forced to on or off, regardless of the
  template sensor helper's state.

## How to build the templates

### Based on another entity's state

The most simple use case is based on another entity's state. This can be a switch, light, or any
other entity. You can use `is_state`, `state_attr` or any other templating function to check the
state of another entity.

```jinja
Is the light on? {{ is_state("light.courtyard_door", "on") }}
What is the sun's elevation? {{ state_attr("sun.sun", "elevation") }}
```

For the purpose of automating a control group, the template should return the state (and optionally
a description, separated by a comma)

```jinja
{% if is_state("light.courtyard_door", "on") %}
  on,The courtyard door light is on
{% else %}
  off
{% endif %}
```

You can even save it in a variable to use in more complex tests

```jinja
{% set ld = is_state("light.courtyard_door", "on") %}
{% set el = state_attr("sun.sun", "elevation") %}
{% if ld or el < -4 %}
  on,The courtyard door light is on or sun has set
{% else %}
  off
{% endif %}
```

For more descriptive debug messages, it might be better to write the template as follows. In this
case the switch is more important and will return first.

```jinja
{% if is_state("light.courtyard_door", "on") %}
  on,The courtyard light is switched on
{% elif state_attr("sun.sun", "elevation") < -4 %}
  on,The sun has set
{% else %}
  off
{% endif %}
```

### Jinja recipes

Here are some Jinja recipes that can be used to construct the template.

#### Movement detected (change in last x seconds)

For detecting movement, you can use the last_changed attribute of a PIR (typically a binary_sensor)
or even a door sensors (binary sensor indicating open/close)

```jinja
{% set n = as_timestamp(now()) %}
{% set change_s = n-(as_timestamp(states.binary_sensor.zone_agter_buite_open.last_changed) or n) %}

Time since last change: {{ change_s }} seconds
Movement in last 5 min: {{ change_s < 300 }}
```

This is done by comparing the *timestamps* of the current time, returned by `as_timestamp(now())`,
with the timestamp of the entity's last_changed. I prefer to save the current time in a variable, so
that you can reuse it for multiple motion inputs. You will also see that I used it twice in the
movement step, the second `or n` covers the case when there is no last_changed state. This helps
with debugging, if you have the wrong entity name it will always be true. The side effect is that it
will also trigger this particular motion when you restart Home Assistant. If you don't like this use
`or 0` instead of `or n`. Not having `or <some-default>` will raise an error when it's unavailable.

#### Time based

Between 7:00 and 8:30 in the evening. Note how we use 24h time to differentiate between AM/PM.

```jinja
{% set t = now().strftime('%T') %}
{% set evening_timeslot = t >= '19:00:00' and t <= '20:30:00' %}
```

#### Day / night and schedule attributes

Instead of (or in addition to) sun elevation, a dedicated day/night binary sensor is often clearer.
Custom attributes on that sensor can hold schedule flags (for example kitchen hours):

```jinja
{% set dark = is_state("binary_sensor.day", "off") %}
{% set ktime = state_attr("binary_sensor.day", "kitchen") | bool(False) %}

{% if dark %}
  on,dark
{% elif ktime %}
  on,kitchen schedule
{% else %}
  off
{% endif %}
```

#### Timeout multiplier (override extends motion windows)

Use a button/switch as a temporary override that *lengthens* motion timeouts instead of forcing the
light permanently on. `iif` picks the multiplier:

```jinja
{%- set x = iif(is_state("binary_sensor.garage_switch_1", "on"), 5, 1) -%}
{%- set n = as_timestamp(now()) -%}
{%- if 600*x > (n-(as_timestamp(states.binary_sensor.zone_garage_pir_open.last_changed) or n)) -%}
  on,garage movement
{%- else -%}
  off
{%- endif -%}
```

When the override is on, a 10-minute window becomes 50 minutes (`600*5`).

#### Numeric brightness / level targets

For dimmable lights or flood levels, return a number (`0` / `100`) instead of `on` / `off`. An
`input_number` helper is a convenient manual override:

```jinja
{%- set lp = states("input_number.light_patio") | int(0) -%}
{{ iif(lp, 100, 0) }}
```

Or combine with darkness and motion:

```jinja
{%- set dark = is_state("binary_sensor.day", "off") -%}
{%- set n = as_timestamp(now()) -%}
{%- set gate = 360 > (n-(as_timestamp(states.binary_sensor.gate_open.last_changed) or n)) -%}
{{ iif(dark and gate, 100, 0) }}
```

#### Ignore ESPHome reconnect false triggers

When an ESPHome device reconnects, every entity on that device gets a fresh `last_changed` even if
nothing physically changed. If you treat a switch's `last_changed` as a button press, also require
the device status entity to be older than the switch change:

```jinja
{%- set n = as_timestamp(now()) -%}
{%- set btntv = int(n-(as_timestamp(states.binary_sensor.tv_switch_1.last_changed) or n)) -%}
{%- set tvstatus = int(n-(as_timestamp(states.binary_sensor.tv_status.last_changed) or n)) -%}
{%- set dark = is_state("binary_sensor.day", "off") -%}

{%- if dark and btntv < 300 and tvstatus > (btntv + 30) -%}
  on,BTNTV,btntv={{ btntv }},tvstatus={{ tvstatus }}
{%- else -%}
  off
{%- endif -%}
```

On reconnect, `tvstatus ≈ btntv`, so the condition fails. A real switch press while the device has
been online keeps `tvstatus` large and still fires.

## Full Examples

These examples combine the concepts discussed earlier. I have many of these, especially for security
lights outside the house, where you want to ensure they are only on when needed and they are
typically switched by individual sonoffs devices all around the house.

This allows them to be motion based (movement in that area), time based (early evening when we're
awake), or have a quick override (when we are outside, the alarm went off, etc.)

### Example 1

Here we control the light in the scullery, which is between the laundry and the kitchen. It should
be on when either:

- The kitchen light is on
- The laundry light is on
- If there has been motion in the scullery in the last 5 minutes (`ss<300`)
- If there has been motion in the kitchen in the last 5 minutes, the motion timer in the scullery
  increases to 10 minutes (`sk<300 and ss<600`)

```jinja
{%- if is_state("light.db2_kitchen", "on") -%}
  on,light kitchen
{%- elif is_state("light.lt3_laundry", "on") -%}
  on,light laundry
{%- else -%}
  {%- set n = as_timestamp(now()) -%}
  {%- set sk = (n-(as_timestamp(states.binary_sensor.zone_kitchen_open.last_changed) or n)) -%}
  {%- set ss = (n-(as_timestamp(states.binary_sensor.zone_scullery_open.last_changed) or n)) -%}
  {%- if (sk<300 and ss <600) or (ss<300) -%}
    on,movement kitchen/scullery
  {%- else -%}
    off
  {%- endif -%}
{%- endif -%}
```

### Example 2

The following example is from the garage. Motion and door sensors drive the light, and a physical
switch on the ESPHome device acts as a timeout multiplier (5×) rather than a hard on/off override.

So the light will be on:

- When there has been movement in the garage (10 min, or 50 min with override)
- When the house garage door has changed (200 s, or ~17 min with override)
- When garage door C or J has changed in the last 5 minutes

```jinja
{%- set x = iif(is_state("binary_sensor.garage0_switch_1", "on"), 5, 1) -%}
{% set n = as_timestamp(now()) -%}
{%- if 600*x > (n-(as_timestamp(states.binary_sensor.zone_garage_pir_open.last_changed) or n)) -%}
  on,garage movement
{%- elif 200*x > (n-(as_timestamp(states.binary_sensor.zone_garage_huis_open.last_changed) or n)) -%}
  on,garage door
{%- elif 300 > (n-(as_timestamp(states.binary_sensor.zone_garage_c_open.last_changed) or n)) -%}
  on,garage c
{%- elif 300 > (n-(as_timestamp(states.binary_sensor.zone_garage_j_open.last_changed) or n)) -%}
  on,garage j
{%- else -%}
  off
{%- endif -%}
```
