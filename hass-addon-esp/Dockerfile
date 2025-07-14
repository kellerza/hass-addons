ARG BUILD_FROM
FROM ${BUILD_FROM}

LABEL maintainer="Johann Kellerman <kellerza@gmail.com>"

# Add uv to the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Install sunsynk from local source
COPY ha_addon ha_addon

RUN set -x \
    && curl -LsSf https://astral.sh/uv/0.7.20/install.sh | sh \
    && uv venv \
    && uv pip install --index-strategy unsafe-best-match \
        ./ha_addon

COPY rootfs /
