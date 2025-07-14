ARG BUILD_FROM
FROM ${BUILD_FROM}

LABEL maintainer="Johann Kellerman <kellerza@gmail.com>"

# Add uv to the `PATH`
ENV PATH="/root/.local/bin/:$PATH"
ENV HIDAPI_WITH_LIBUSB=1

# Required to build hidapi
RUN apk add --no-cache --virtual .build-deps \
      build-base zlib-dev openssl-dev libffi-dev \
      hidapi \
      eudev-libs eudev-dev libusb-dev libusb

# Install qsusb64 from local source
COPY ha_addon ha_addon

RUN set -x \
    && curl -LsSf https://astral.sh/uv/0.7.15/install.sh | sh \
    && uv venv \
    && uv pip install --index-strategy unsafe-best-match \
        ./ha_addon[hidapi]

COPY rootfs /
