FROM python:3.11-slim

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get -y upgrade

WORKDIR /app

COPY requirements.txt /app

RUN --mount=type=cache,target=/root/.cache/pip python -m pip install -r requirements.txt

COPY /stac_fastapi_ingester /app/stac_fastapi_ingester

CMD ["python", "-m", "stac_fastapi_ingester", "transformed", "subscribe", "--prefix", "stac-fastapi"]
