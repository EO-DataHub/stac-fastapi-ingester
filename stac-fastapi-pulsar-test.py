from random import choice
from string import ascii_uppercase
from time import sleep
from typing import Optional
import os

import json
import requests

import click
import pulsar
import pulsar.exceptions
import boto3

INTERVAL = 1


@click.group()
@click.argument("topic", type=str)
@click.pass_context
def cli(ctx, topic: str):
    ctx.ensure_object(dict)
    pulsar_url = os.getenv("PULSAR_URL", "")
    ctx.obj["CLIENT"] = pulsar.Client(pulsar_url)
    ctx.obj["TOPIC"] = topic
    click.echo(f"Connecting to broker '{pulsar_url}' with topic '{topic}'")


@cli.command()
@click.option("--prefix", type=str, default=None)
@click.option("-n", type=int, default=100, show_default=True)
@click.pass_context
def publish(ctx, prefix: Optional[str] = None, n: Optional[int] = 100):
    """
    Publish n messages to Pulsar broker.
    """
    prefix = prefix or "".join(choice(ascii_uppercase) for _ in range(6))
    client: pulsar.Client = ctx.obj["CLIENT"]
    topic: str = ctx.obj["TOPIC"]
    producer: pulsar.Producer = client.create_producer(topic=topic, producer_name=prefix)
    harvested_dict = {"added_keys": ["catalogue-data/supported/collections/cmip6/items/CMIP6.ScenarioMIP.CSIRO-ARCCSS.ACCESS-CM2.ssp126.r1i1p1f1.day.tasmin.gn.v20210317.json", 
                                      "catalogue-data/supported/collections/cmip6/items/CMIP6.ScenarioMIP.CSIRO-ARCCSS.ACCESS-CM2.ssp126.r1i1p1f1.day.pr.gn.v20210317.json", 
                                      "catalogue-data/supported/collections/cmip6.json", 
                                      "catalogue-data/supported/collections/cordex.json",],
                      "updatedkeys": ["catalogue-data/supported/collections/cmip6/items/CMIP6.ScenarioMIP.CSIRO-ARCCSS.ACCESS-CM2.ssp126.r1i1p1f1.day.pr.gn.v20210317.json",],
                      "deleted_keys": ["catalogue-data/supported/collections/cordex.json",],
                      "bucket_name": "catalogue-data",
                    }

    harvested_string = json.dumps(harvested_dict)
    try:
        for ii in range(n):
            msg = harvested_string
            click.echo(msg)
            producer.send(msg.encode("utf-8"))
            sleep(INTERVAL)
    finally:
        producer.close()
        client.close()


if __name__ == "__main__":
    cli(obj={})