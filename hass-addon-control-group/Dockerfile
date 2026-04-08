FROM ghcr.io/home-assistant/base-python:3.14-alpine3.23
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

LABEL maintainer="Johann Kellerman <kellerza@gmail.com>"

# Add uv to the PATH
ENV PATH="/root/.local/bin/:$PATH"

COPY ha_addon .

RUN cat ~/.config/uv/uv.toml \
    && uv config show \
    && rm -rf ~/.config/uv/uv.toml

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN set -x \
    && uv sync --locked --no-dev

COPY rootfs /
