FROM ghcr.io/home-assistant/base-python:3.14-alpine3.23
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

LABEL maintainer="Johann Kellerman <kellerza@gmail.com>"

# Add uv to the PATH
ENV PATH="/root/.local/bin/:$PATH"

COPY ha_addon .

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN set -x \
    #&& curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh \
    && uv sync --locked --no-dev

COPY rootfs /
