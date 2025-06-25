# QSUSB64

Run

```bash
uv lock --upgrade && uv sync
uv run python -m qsusb64
```

## Monitor logs from ssh

```bash
ssh homeassistant.local

while :
do
    docker logs -f --tail 50 addon_local_hass-addon-qsusb64
done
```
