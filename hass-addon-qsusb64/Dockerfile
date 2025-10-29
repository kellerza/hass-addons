ARG BUILD_FROM
FROM ${BUILD_FROM}

ARG UV_VERSION=0.9.5

LABEL maintainer="Johann Kellerman <kellerza@gmail.com>"

# Add uv to the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Required to build hidapi
ENV HIDAPI_WITH_LIBUSB=1
RUN apk add --no-cache --virtual .build-deps \
      build-base \
      eudev-dev=3.2.14-r5 \
      eudev-libs=3.2.14-r5 \
      hidapi=0.14.0-r0 \
      libffi-dev=3.4.8-r0 \
      libusb-dev=1.0.28-r0 \
      libusb=1.0.28-r0 \
      openssl-dev=3.5.4-r0 \
      zlib-dev=1.3.1-r2

COPY ha_addon .

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN set -x \
    && curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh \
    && uv sync --locked --no-dev --extra hidapi

COPY rootfs /
