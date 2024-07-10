FROM python:3.11-slim

RUN apt-get update && \
    apt-get -y upgrade

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY /stac_fastapi_ingester /app/stac_fastapi_ingester

CMD ["python", "-m", "stac_fastapi_ingester", "transformed", "subscribe", "--prefix", "stac-fastapi"]
