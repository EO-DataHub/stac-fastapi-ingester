from random import choice
from string import ascii_uppercase
from time import sleep
from typing import Optional

import json
import requests

import click
import pulsar
import pulsar.exceptions
import boto3

INTERVAL = 1


@click.group()
@click.argument("pulsar_url", type=str)
@click.argument("topic", type=str)
@click.pass_context
def cli(ctx, pulsar_url: str, topic: str):
    ctx.ensure_object(dict)
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
    harvested_dict = {"added_files": ["item_1.json", "item_2.json"],
                      "deleted_files": ["item_3.json"],
                      "updated_files": ["item_4.json", "item_5.json", "item_6.json"],
                      "repo": {"source": "/link_to_resource_catalog/"}
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

################################
### DELETE FROM STAC FASTAPI ###
################################

def delete_collection(api_url, collection_id):
    headers = {"accept": "application/json"}
    try:
        resp = requests.delete(
            f"{api_url}/collections/{collection_id}", 
            headers=headers,
        )
        if resp.status_code == 200:
            print(f"Status code: {resp.status_code}")
        elif resp.status_code == 409:
            print(f"Status code: {resp.status_code}")
    except requests.ConnectionError:
        click.secho("failed to connect")
    except:
        print("Something went wrong")

def delete_item(api_url, collection_id, item_id):
    headers = {"accept": "application/json"}
    try:
        resp = requests.delete(
            f"{api_url}/collections/{collection_id}/items/{item_id}", 
            headers=headers,
        )
        if resp.status_code == 200:
            print(f"Status code: {resp.status_code}")
        elif resp.status_code == 409:
            print(f"Status code: {resp.status_code}")
    except requests.ConnectionError:
        click.secho("failed to connect")
    except:
        print("Something went wrong")

##############################
### UPDATE IN STAC FASTAPI ###
##############################       

def update_collection(api_url, collection_id, data):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.put(
            f"{api_url}/collections", 
            headers=headers,
            json=data,
        )
        if resp.status_code == 200:
            print(f"Status code: {resp.status_code}")
        elif resp.status_code == 409:
            print(f"Status code: {resp.status_code}")
    except requests.ConnectionError:
        click.secho("failed to connect")
    except:
        print("Something went wrong")

def update_item(api_url, collection_id, item_id, data):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.put(
            f"{api_url}/collections/{collection_id}/items/{item_id}", 
            headers=headers,
            json=data,
        )
        if resp.status_code == 200:
            print(f"Status code: {resp.status_code}")
        elif resp.status_code == 409:
            print(f"Status code: {resp.status_code}")
    except requests.ConnectionError:
        click.secho("failed to connect")
    except:
        print("Something went wrong")


################################
### CREATE IN STAC FASTAPI ###
################################

def create_collection(api_url, collection_id):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            f"{api_url}/collections/{collection_id}", 
            headers=headers,
        )
        if resp.status_code == 200:
            print(f"Status code: {resp.status_code}")
        elif resp.status_code == 409:
            print(f"Status code: {resp.status_code}")
    except requests.ConnectionError:
        click.secho("failed to connect")
    except:
        print("Something went wrong")

def create_item(api_url, collection_id, item_id, data):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            f"{api_url}/collections/{collection_id}/items/{item_id}", 
            headers=headers,
            json=data,
        )
        if resp.status_code == 200:
            print(f"Status code: {resp.status_code}")
            return True
        elif resp.status_code == 404:
            ## Add files awaiting collection creation to the end of the list again
            return False
            #awaiting_collection.append(file_uri)
        elif resp.status_code == 409:
            print(f"Status code: {resp.status_code}")
    except requests.ConnectionError:
        click.secho("failed to connect")
    except:
        print("Something went wrong")


def interpret_message(msg: str, api_url):

    ## Configure boto3 client ready for data access
    client = boto3.client("s3")

    updates_json = json.loads(msg)

    ## Extract file names into actions lists
    files_to_update = updates_json['updated_files']
    files_to_delete = updates_json['deleted_files']
    files_to_create = updates_json['added_files']

    ## Filter by file types - Collections and FeatureCollections
    files_to_create_collections = [file_uri for file_uri in files_to_create if file_uri.rsplit("/",2)[1] == "collections"]
    files_to_create_other = [file_uri for file_uri in files_to_create if file_uri.rsplit("/",2)[1] != "collections"]

    files_to_update_collections = [file_uri for file_uri in files_to_update if file_uri.rsplit("/",2)[1] == "collections"]
    files_to_update_other = [file_uri for file_uri in files_to_update if file_uri.rsplit("/",2)[1] != "collections"]

    files_to_delete_collections = [file_uri for file_uri in files_to_delete if file_uri.rsplit("/",2)[1] == "collections"]
    files_to_delete_other = [file_uri for file_uri in files_to_delete if file_uri.rsplit("/",2)[1] != "collections"]

    ## First we need to delete items and collections
    for file_url in files_to_delete:
        ## We can track deleted collections as this will also delete all associated items so no need to call the delete items endpoint as well
        deleted_collections = {}

        bucket, key = file_url.replace("s3://","").split("/",1)
        data = client.get_object(Bucket=bucket, Key=key)
        data = json.loads(data['Body'].read())

        if data['type'] == "Collection":
            collection_id = data['id']
            deleted_collections.add(collection_id)
            delete_collection(api_url, collection_id)

        elif data['type'] == "Feature":
            collection_id = data['collection']
            if collection_id in deleted_collections:
                continue
            item_id = data['id']
            delete_item(api_url, collection_id, item_id)

    ## Now create new collections and items
    num_files_to_create = len(files_to_create)
    files_count = 0
    
    for file_uri in files_to_create:

        ## Variable to prevent looping status, limits number of loops to at most 2
        if files_count >= num_files_to_create * 2:
            break

        bucket, key = file_uri.replace("s3://","").split("/",1)
        data = client.get_object(Bucket=bucket, Key=key)
        data = json.loads(data['Body'].read())
        if data['type'] == "Collection":
            collection_id = data['id']
            create_collection(api_url, collection_id)

        elif data['type'] == "Feature":
            collection_id = data['collection']
            item_id = data['id']
            ## Handle case in which collection is not yet created for this item
            item_registered = create_item(api_url, collection_id, item_id, data)
            files_to_create.append(file_uri) if not item_registered else None

        ## Increment loop counter
        files_count+=1
            

    ## Now update collections and items
    for file_uri in files_to_update:
        bucket, key = file_uri.replace("s3://","").split("/",1)
        data = client.get_object(Bucket=bucket, Key=key)
        data = json.loads(data['Body'].read())
        if data['type'] == "Collection":
            update_collection(api_url, collection_id, data)
        elif data['type'] == "Feature":
            collection_id = data['collection']
            item_id = data['id']
            update_item(api_url, collection_id, item_id, data)



@cli.command()
@click.argument("api_url", type=str)
@click.option("--prefix", type=str, default=None)
@click.pass_context
def subscribe(ctx, api_url: str, prefix: Optional[str] = None):
    """
    Subscribe to messages from a Pulsar broker.
    """

    prefix = prefix or "".join(choice(ascii_uppercase) for _ in range(6))
    client: pulsar.Client = ctx.obj["CLIENT"]
    topic: str = ctx.obj["TOPIC"]
    consumer = client.subscribe(topic=topic, subscription_name=prefix)
    try:
        while True:
            msg = consumer.receive()
            interpret_message(msg.data(), api_url)
            consumer.acknowledge(msg)
    except pulsar.exceptions.Interrupted:
        pass
    except Exception:
        consumer.negative_acknowledge(msg)
    finally:
        consumer.close()
        client.close()


if __name__ == "__main__":
    cli(obj={})