# QSUSB64 add-on

This is a Home Assistant addon for controlling QwikSwitch devices with the QwikSwitch USB modem.

Features:

- Connects directly to the QwikSwitch USB modem (No QSUSB software required)
- Publishes entities to Home Assistant and supports MQTT discovery
- The following devices are supported:
  - Buttons (events on a HA device - MQTT Device Trigger)
  - Switches (ON/OFF, MQTT Switch)
  - Lights (ON/OFF, MQTT Light)
  - Dimmers (ON/OFF & brightness, brightness - MQTT Light) * *Not well tested yet*

This should cover a wide range of QwikSwitch relays, buttons and dimmers. No power measurement is supported. You are welcome to have a look at the code and enhance the **qs_decode** function to decode anything not supported.

## Installation

1. Add this repository to your HA Supervisor

   [![Open your Home Assistant instance and add the kellerza/hass-addons URL](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fkellerza%2Fhass-addons)

2. Install the addon, configure and run.

## Motivation

I originally built the Home Assistant QwikSwitch USB [integration](https://www.home-assistant.io/integrations/QwikSwitch/) back in 2016. It connects to the official QwikSwitch QSUSB software. A colleague published a Home Assistant [addon](https://github.com/nardusleroux/hassio-qsusb) that allows you to install QSUSB on the HA Operating System.

Unfortunately the QSUSB software is 32-bit only and attempts to build a 64-bit addon has not been successful. With Home Assistant deprecating 32-bit platform support, I decided to build a new addon that does not depend on the QSUSB software.

QwikSwitch devices are still widely available in South Africa, understood by local electricians, and used in several homes (including my own :wink:). I would definitely still consider using them for your smart home. They are reliable, easy to install and configure, and have a wide range of devices available.

The intention is not to cover all function of the existing QSUSB software, or even all devices, but rather to cover my own use case to have a reliable way to control my QwikSwitch devices from Home Assistant. If you want to add support for another device, you are welcome to submit a PR.

## Development

You can test the addon locally by cloning the repository and running it in a Python 3.12+ virtual environment.

Requirements: [uv](https://docs.astral.sh/uv/getting-started/). uv can be used to install Python and the required dependencies in a virtual environment.

The `hidapi` Python package works on Windows & Linux. In the addon it uses libudev & libusb to access the USB device.

Once you have cloned the repository, you can install the dependencies & run the addon from the working directory using the following commands:

```bash
uv sync
uv run python -m qsusb64
```

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
