FROM python:3.10-slim

RUN apt-get update && \
    apt-get -y upgrade

WORKDIR /app

COPY stac-fastapi-pulsar /app/stac-fastapi-pulsar

COPY requirements.txt /app

RUN pip install -r requirements.txt

CMD ["python", "-m", "stac-fastapi-pulsar", "pulsar://127.0.0.1:6650", "transformed", "subscribe", "https://dev.eodatahub.org.uk/stac-fastapi", "--prefix", "stac-fastapi"]
