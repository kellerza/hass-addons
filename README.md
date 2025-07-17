# Home Assistant add-ons by @kellerza

[![Open your Home Assistant instance and add the kellerza/hass-addons URL](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fkellerza%2Fhass-addons)

This repository contains various Home Assistant add-ons

- Sunsynk/Deye Inverter: An add-on for monitoring and controlling Sunsynk and Deye inverters - see <https://kellerza.github.io/sunsynk/>
- SMA Energy Meter: An add-on for monitoring SMA Energy Meters - see <https://github.com/kellerza/hassio-sma-em>. Including a supporting mbusdb addon
- QSUSB64: An add-on for controlling QwikSwitch devices with the QwikSwitch USB modem - see [hass-addon-qsusb64/README.md](hass-addon-qsusb64/README.md)
- ESP: An add-on for monitoring South African load shedding schdules via the EskonSEPush API - see <https://kellerza.github.io/sunsynk/guide/esp>
- Git-push: An add-on for pushing files to a remote Git repository

## Development

You can test the addon locally by cloning the repository and running it in a Python 3.12+ virtual environment.

Requirements: [uv](https://docs.astral.sh/uv/getting-started/). uv can be used to install Python and the required dependencies in a virtual environment.

When you run it on your local machine, it will use config from `<working-dir>/.data/options.yaml`. As a starting point you can copy the config under the **options:** key from [config.yaml](./hass-addon-qsusb64/config)

## Monitor logs from ssh

```bash
ssh homeassistant.local

while :
do
    docker logs -f --tail 50 addon_local_hass-addon-qsusb64
    echo "Press Ctrl+C to exit"
    sleep 0.5
done
```
