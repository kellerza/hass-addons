ARG BUILD_FROM
FROM ${BUILD_FROM}

LABEL maintainer="Johann Kellerman <kellerza@gmail.com>"

# Add uv to the PATH
ENV PATH="/root/.local/bin/:$PATH"

COPY ha_addon .

RUN set -x \
    && curl -LsSf https://astral.sh/uv/0.8.19/install.sh | sh \
    && uv sync --locked --no-dev

COPY rootfs /
