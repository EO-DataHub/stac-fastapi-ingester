FROM python:3.11-slim

RUN apt-get update && \
    apt-get -y upgrade

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY /stac-fastapi-ingester /app/stac-fastapi-ingester

CMD ["python", "-m", "stac-fastapi-ingester", "transformed", "subscribe", "--prefix", "stac-fastapi"]
