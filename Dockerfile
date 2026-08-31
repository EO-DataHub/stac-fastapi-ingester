# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update --yes --quiet \
    && apt-get install --yes --quiet --no-install-recommends \
    openssh-client \
    procps \
    git \
    g++

ENV UV_NO_DEV=1
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Copy project files
COPY . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

CMD ["uv", "run", "--no-sync", "python", "-m", "stac_fastapi_ingester", "transformed", "subscribe", "--prefix", "stac-fastapi"]
