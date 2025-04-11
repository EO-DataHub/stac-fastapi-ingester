FROM python:3.12-slim

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update --yes --quiet \
    && apt-get install --yes --quiet --no-install-recommends \
    openssh-client \
    procps \
    git

WORKDIR /app

COPY requirements.txt /app

RUN --mount=type=cache,target=/root/.cache/pip python -m pip install -r requirements.txt

COPY /stac_fastapi_ingester /app/stac_fastapi_ingester

CMD ["python", "-m", "stac_fastapi_ingester", "transformed", "subscribe", "--prefix", "stac-fastapi"]
