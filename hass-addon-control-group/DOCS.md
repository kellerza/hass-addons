# Control group add-on

## Jinja recipes

Here are some Jinja recipes that can be used in the template to control the cgroup.
These can be used in the `template` option of the cgroup.

### Based on another switch/light state

Either of these can be used. If you use bool, you need to provide a default value (false).

```jinja
{% set ld2 = is_state("light.courtyard_door", "on") %}
{% set ld1 = bool(states("light.courtyard_door"), false) %}

The other light is on: {{ ld1}} {{ ld2 }} {{ ld1==ld2 }}
```

### Movement detected (change in last x seconds)

```jinja
{% set n = as_timestamp(now()) %}
{% set dif = n-(as_timestamp(states.binary_sensor.zone_agter_buite_open.last_changed) or n) %}

Seconds since last change: {{ dif }}
Movement in last 5 min: {{ div < 300 }}
```

### Time based

Between 7 and 8 in the evening

```jinja
{% set t = now().strftime('%T') %}

{{ iif(t >= '19:00:00' and t <= '20:30:00', 100, 0) }}
```
