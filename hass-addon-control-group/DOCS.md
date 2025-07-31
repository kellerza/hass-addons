# Control group add-on

The control group add-on allows you to automate entities, typically lights and switches, based on the result of a template.

This allows you to easily build motion or presence-based automations using the state of other entities:

- When did they last change (indicating movement for PIR, or binary_sensors)
- When a button was pressed
- The state of another switch, light or basically any entity's state or attribute.
- During the evening, when the sun sets, or based on a specific time of the day

The template can be as simple or as complex as you need it to be. You can add a reason to your desired state, which makes it really easy to debug and fine-tune your automations.

Templates are standard Home Assistant [templates](https://www.home-assistant.io/docs/configuration/templating/). The sections below shows several examples.

## Alternative options

A similar concept can be achieved using a combination of existing Home Assistant features:

- You can use *template sensor* helpers to create the state and use an automation that syncs the value of this template sensor to the desired entity.
In the past I've used automation blueprints to maintain this syncing capability. You end up with several entities that you need to manage and it's fairly cumbersome to debug.

- Home Assistant has [Template Triggers](https://www.home-assistant.io/docs/automation/trigger/#template-trigger) that can be used for automations, but unfortunately only when the template state changes from False to True. For some discussions see [PR#121451](https://github.com/home-assistant/core/pull/121451).

## Installation

1. Add the *hass-addons* repository to your Home Assistant

   [![Open your Home Assistant instance and add the kellerza/hass-addons URL](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fkellerza%2Fhass-addons)

2. Install the addon, configure and run.

## Configuration

Groups are configured under the **GROUPS** key in the configuration file.

When a group has a **TEMPLATE** defined, it will be rendered whenever the state changes in Home Assistant. The result of the template will be used to determine the state of the group. Template are discussed in detail in the next sections.

Each group requires a unique **ID**. The ID can be a short string as it will include a uuid for the addon when used as identifiers for Home Assistant entities. If you change them you will get stale entities that you can delete from the frontend (after a restart!)

You can add a **NAME**. If not provided the name will be a list of entities.

The **ENTITIES** in a group can either be a name (light.x, switch.y), or a template that will be expanded when the addon starts.

Example:

```yaml
GROUPS:
- ID: abc
  ENTITIES:
    - light.fixed_light
    - "{{ states.binary_sensor | map(attribute='entity_id') | select('is_state', 'on') | list }}"
  CALL_SCRIPTS: script.do_something
```

Using **CALL_SCRIPT** you can call a script when the result of the template changes. This is optional and the value of the template will be passed to the script as *msg*

```yaml
GROUPS:
- ID: abc
  ENTITIES: [...]
  CALL_SCRIPT: script.do_something
```

## How to build the templates

### Based on another entity's state

The most simple use case is based on another entity's state. This can be a switch, light, or any other entity. You can use `is_state`, `state_attr` or any other templating function to check the state of another entity.

```jinja
Is the light on? {{ is_state("light.courtyard_door", "on") }}
What is the sun's elevation? {{ state_attr("sun.sun", "elevation") }}
```

For the purpose of automating a control group, the template should return the state (and optionally a description, separated by a comma)

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

For more descriptive debug messages, it might be better to write the template as follows. In this case the switch is more important and will return first.

```jinja
{% if is_state("light.courtyard_door", "on") %}
  on,The courtyard light is switched on
{% elif state_attr("sun.sun", "elevation") < -4 %}
  on,The sun has set
{% else %}
  off
{% endif %}
```

### How to debug the templates

You can add the following card to your homeassistant frontend. It will use a markdown card to display all the entities being controlled, their state and the reason for the state (from the template!)

This will allow you to quickly fine-tune your templates.

```yaml
type: markdown
content: "{{ states('sensor.cgroup_debug') }}"
title: Control group debug
```

The `sensor.cgroup_debug` entity will be added to your Home Assistant instance.

### Jinja recipes

Here are some Jinja recipes that can be used in the `template` option of the group.

#### Movement detected (change in last x seconds)

For detecting movement, you can use the last_changed attribute of a PIR (typically a binary_sensor) or even a door sensors (binary sensor indicating open/close)

```jinja
{% set n = as_timestamp(now()) %}
{% set change_s = n-(as_timestamp(states.binary_sensor.zone_agter_buite_open.last_changed) or n) %}

Time since last change: {{ change_s }} seconds
Movement in last 5 min: {{ change_s < 300 }}
```

This is done by comparing the *timestamps* of the current time, returned by `as_timestamp(now())`, with the timestamp of the entity's last_changed. I prefer to save the current time in a variable, so that you can reuse it for multiple motion inputs. You will also see that I used it twice in the movement step, the second `or n` covers the case when there is no last_changed state. This helps with debugging, if you have the wrong entity name it will always be true. The side effect is that it will also trigger this particular motion when you restart Home Assistant. If you don't like this use `or 0` instead of `or n`. Not having `or <some-default>` will raise an error when it's unavailable.

#### Time based

Between 7:00 and 8:30 in the evening. Note how we use 24h time to differentiate between AM/PM.

```jinja
{% set t = now().strftime('%T') %}

{{ set evening_timeslot = t >= '19:00:00' and t <= '20:30:00' }}
```

## More Examples

These examples combine the concepts discussed earlier. I have many of these, especially for security lights outside the house, where you want to ensure they are only on when needed and they are typically switched by individual sonoffs devices all around the house.

This allows them to be motion based (movement in that area), time based (early evening when we're awake), or have a quick override (when we are outside, the alarm went off, etc.)

### Example 1

Here we control the light in the scullery, which is between the laundry and the kitchen. It should on when either:

- The kitchen light is on
- The laundry light is on
- If there has been motion in the scullery in the last 5 minutes (`ss<300`)
- If there has been motion in the kitchen in the last 5 minutes, the motion timer in the scullery increases to 10 minutes (`sk<300 and ss<600`)

```yaml
GROUPS:
  - ID: abc
    ENTITIES: [light.scullery]
    TEMPLATE: |
      {%- if is_state("light.kitchen", "on") -%}
        on,light kitchen
      {%- elif is_state("light.laundry", "on") -%}
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
      {%- endif %}
```

### Example 2

The following example is from the garage. It has a motion sensor and the light is controlled from a sonoff. The sonoff's status led can be toggled by pressing the button and this indicates an override state for the light relay on the sonoff.

So the light will be on:

- When there has been movement in the garage in the last 5 minutes
- When the garage door has been opened/closed in the last 200 seconds (3m20s)
- When the override is on (a press button toggling the sonoff's status led)

```yaml
GROUPS:
  - ID: abc
    ENTITIES: [light.garage]
    TEMPLATE: |
      {%- set n = as_timestamp(now()) -%}
      {%- if 600 > (n-(as_timestamp(states.binary_sensor.zone_garage_pir_open.last_changed) or n)) -%}
        on,garage movement
      {%- elif 200 > (n-(as_timestamp(states.binary_sensor.zone_garage_huis_open.last_changed) or n)) -%}
        on,garage door
      {%- elif is_state("light.garage_status_led", "on") -%}
        on,garage override
      {%- else -%}
        off
      {%- endif %}
```
