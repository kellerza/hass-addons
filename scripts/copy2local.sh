#!/bin/sh
# Copy an add-on to the local HA add-ons share for testing.
# Override destination: DEST=/path/to/addons ./scripts/copy2local.sh
cd "$(dirname "$0")/.." || exit 1

DEST="${DEST:-/Volumes/addons}"
VER=$(awk 'BEGIN { srand(); print int(rand() * 100) + 1 }')

print() {
  echo
  echo "$1"
  echo "==========================================================="
  echo
}

# rsync patterns equivalent to scripts/copyexclude.txt (xcopy substring match)
rsync_excl() {
    rsync -a --inplace \
        --exclude '__pycache__' \
        --exclude '*.egg-info' \
        --exclude '.*' \
        --exclude 'tests' \
        --exclude '.mypy_cache' \
        --exclude 'config.localtest.yaml' \
        --exclude 'config.yaml' \
        "$@"
}

copy_package_hass_addons() {
  print "Copy package for '$1'"
  mkdir -p "$DEST/$1/ha_addon"
  for f in pyproject.toml LICENSE README.md uv.lock; do
    cp -f "$f" "$DEST/$1/ha_addon/"
  done
  rsync_excl src/ "$DEST/$1/ha_addon/src/"
}

copy_addon() {
  addon=$1
  print "Copy '$addon' to '$DEST/$addon'"
  mkdir -p "$DEST/$addon"
  rsync_excl "$addon/" "$DEST/$addon/"

  cf="$addon/config.localtest.yaml"
  sed -e 's/image:/# image:/' \
      -e 's/name: /name: A_LOCAL /' \
      -e "s/version: \"/version: \"v${VER}_/" \
      "$addon/config.yaml" >"$cf"
  cp "$cf" "$DEST/$addon/config.yaml"
}


THE_ADDON=hass-addon-qsusb64
#THE_ADDON=hass-addon-control-group
#THE_ADDON=hass-addon-esp

print "Set version to v$VER for local testing of '$THE_ADDON'"
#sh build_prep.sh hass-addon-control-group "$VER"
copy_addon $THE_ADDON
copy_package_hass_addons $THE_ADDON

