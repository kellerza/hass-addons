ARG BUILD_FROM
FROM ${BUILD_FROM}

LABEL maintainer="Johann Kellerman <kellerza@gmail.com>"

# Add uv to the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Required to build hidapi
ENV HIDAPI_WITH_LIBUSB=1
RUN apk add --no-cache --virtual .build-deps \
      build-base zlib-dev openssl-dev libffi-dev \
      hidapi \
      eudev-libs eudev-dev libusb-dev libusb

COPY ha_addon .

RUN set -x \
    && curl -LsSf https://astral.sh/uv/0.9.2/install.sh | sh \
    && uv sync --locked --no-dev --extra hidapi

COPY rootfs /
