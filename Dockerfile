FROM python:3.10-slim

RUN apt-get update && \
    apt-get -y upgrade

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY /stac-fastapi-ingester /app/stac-fastapi-ingester

CMD ["python", "-m", "stac-fastapi-ingester", "pulsar://127.0.0.1:6650", "transformed", "subscribe", "https://dev.eodatahub.org.uk/stac-fastapi", "--prefix", "stac-fastapi"]
