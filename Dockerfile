FROM python:3.11-slim

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get -y upgrade

WORKDIR /app

COPY requirements.txt /app

RUN --mount=type=cache,target=/root/.cache/pip python -m pip install -r requirements.txt

COPY /stac-fastapi-ingester /app/stac-fastapi-ingester

CMD ["python", "-m", "stac-fastapi-ingester", "transformed", "subscribe", "--prefix", "stac-fastapi"]
