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

import logging

# configure boto3 logging
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('boto3').setLevel(logging.CRITICAL)

# create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(filename='stac-fastapi-ingester.log', encoding='utf-8', level=logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


@click.group()
@click.argument("pulsar_url", type=str)
@click.argument("topic", type=str)
@click.pass_context
def cli(ctx, pulsar_url: str, topic: str):
    ctx.ensure_object(dict)
    ctx.obj["CLIENT"] = pulsar.Client(pulsar_url)
    ctx.obj["TOPIC"] = topic
    logger.info(f"Connecting to broker '{pulsar_url}' with topic '{topic}'")


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
            logger.info(f"Status code: {resp.status_code}")
            logger.info(f"Deleted collection {collection_id}")
        elif resp.status_code == 409:
            logger.warning(f"Status code: {resp.status_code}")
        elif resp.status_code == 404:
            logger.warning(f"Status code: {resp.status_code}")
            logger.warning(f"Collection: {collection_id} does not exist.")
    except requests.ConnectionError:
        click.secho("failed to connect")
    except:
        logger.warning("Something went wrong")

def delete_item(api_url, collection_id, item_id):
    headers = {"accept": "application/json"}
    try:
        resp = requests.delete(
            f"{api_url}/collections/{collection_id}/items/{item_id}", 
            headers=headers,
        )
        if resp.status_code == 200:
            logger.info(f"Status code: {resp.status_code}")
            logger.info(f"Deleted item {item_id}")
        elif resp.status_code == 409:
            logger.warning(f"Status code: {resp.status_code}")
        elif resp.status_code == 404:
            logger.warning(f"Status code: {resp.status_code}")
            logger.warning(f"Item: {item_id} in Collection: {collection_id} does not exist.")
    except requests.ConnectionError:
        logger.warning("failed to connect")
    except:
        logger.warning("Something went wrong")

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
            logger.info(f"Status code: {resp.status_code}")
        elif resp.status_code == 409:
            logger.warning(f"Status code: {resp.status_code}")
        elif resp.status_code == 404:
            logger.warning(f"Status code: {resp.status_code}")
            logger.warning(f"Collection {collection_id} not updated as doesn't exist.")
    except requests.ConnectionError:
        logger.warning("failed to connect")
    except:
        logger.warning("Something went wrong")

def update_item(api_url, collection_id, item_id, data):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.put(
            f"{api_url}/collections/{collection_id}/items/{item_id}", 
            headers=headers,
            json=data,
        )
        if resp.status_code == 200:
            logger.info(f"Status code: {resp.status_code}")
        elif resp.status_code == 409:
            logger.warning(f"Status code: {resp.status_code}")
        elif resp.status_code == 404:
            logger.warning(f"Status code: {resp.status_code}")
            response_decoded = json.loads(resp.content.decode())
            response_decoded_description = response_decoded['description']
            if "Item" in response_decoded_description:
                logger.warning(f"Item: {item_id} in Collection: {collection_id} not updated as item doesn't exist.")
            elif "Collection" in response_decoded_description:
                logger.warning(f"Item: {item_id} in Collection: {collection_id} not updated as collection doesn't exist.")
    except requests.ConnectionError:
        logger.warning("failed to connect")
    except:
        logger.warning("Something went wrong")


################################
### CREATE IN STAC FASTAPI ###
################################

def create_collection(api_url, collection_id, data):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            f"{api_url}/collections", 
            headers=headers,
            json=data,
        )
        if resp.status_code == 200:
            logger.info(f"Status code: {resp.status_code}")
        elif resp.status_code == 409:
            logger.warning(f"Status code: {resp.status_code}")
            logger.warning(f"Collection: {collection_id} already exists")
    except requests.ConnectionError:
        logger.warning("failed to connect")
    except:
        logger.warning("Something went wrong")

def create_item(api_url, collection_id, item_id, data):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            f"{api_url}/collections/{collection_id}/items", 
            headers=headers,
            json=data,
        )
        if resp.status_code == 200:
            logger.info(f"Status code: {resp.status_code}")
            return True
        elif resp.status_code == 404:
            ## Add files awaiting collection creation to the end of the list again
            logger.warning(f"Collection: {collection_id} not yet created, will try again in a bit.")
            return False
        elif resp.status_code == 409:
            logger.warning(f"Status code: {resp.status_code}")
            logger.warning(f"Item: {item_id} in Collection: {collection_id} already exists")
            return True
    except requests.ConnectionError:
        logger.warning("failed to connect")
    except:
        logger.warning("Something went wrong")


def interpret_message(msg: str, api_url):

    ## Configure boto3 client ready for data access
    client = boto3.client("s3")

    updates_json = json.loads(msg)

    ## Extract file names into actions lists
    files_to_update = updates_json['updated_files'] if 'updated_files' in updates_json.keys() else []
    files_to_delete = updates_json['deleted_files'] if 'deleted_files' in updates_json.keys() else []
    files_to_create = updates_json['added_files'] if 'added_files' in updates_json.keys() else []

    ## Filter by file types - Collections and FeatureCollections
    # files_to_create_collections = [file_uri for file_uri in files_to_create if file_uri.rsplit("/",2)[1] == "collections"]
    # files_to_create_other = [file_uri for file_uri in files_to_create if file_uri.rsplit("/",2)[1] != "collections"]

    # files_to_update_collections = [file_uri for file_uri in files_to_update if file_uri.rsplit("/",2)[1] == "collections"]
    # files_to_update_other = [file_uri for file_uri in files_to_update if file_uri.rsplit("/",2)[1] != "collections"]

    # files_to_delete_collections = [file_uri for file_uri in files_to_delete if file_uri.rsplit("/",2)[1] == "collections"]
    # files_to_delete_other = [file_uri for file_uri in files_to_delete if file_uri.rsplit("/",2)[1] != "collections"]

    ## Delete items and collections
    for file_url in files_to_delete:
        ## We can track deleted collections as this will also delete all associated items so no need to call the delete items endpoint as well
        deleted_collections = set()

        bucket, key = file_url.replace("s3://","").split("/",1)
        data = client.get_object(Bucket=bucket, Key=key)
        data = json.loads(data['Body'].read())

        if data['type'] == "Collection":
            collection_id = data['id']
            logger.info(f"Deleting collection {collection_id}")
            deleted_collections.add(collection_id)
            delete_collection(api_url, collection_id)

        elif data['type'] == "Feature":
            collection_id = data['collection']
            if collection_id in deleted_collections:
                continue
            item_id = data['id']
            logger.info(f"Deleting item {item_id} in collection {collection_id}")
            delete_item(api_url, collection_id, item_id)

    ## Create new collections and items
    num_files_to_create = len(files_to_create)
    files_count = 0
    
    for file_uri in files_to_create:
        ## Variable to prevent endless looping, limits number of loops to at most 2
        if files_count >= num_files_to_create * 2:
            break

        bucket, key = file_uri.replace("s3://","").split("/",1)
        data = client.get_object(Bucket=bucket, Key=key)
        data = json.loads(data['Body'].read())

        if data['type'] == "Collection":
            collection_id = data['id']
            logger.info(f"Creating collection {collection_id}")
            create_collection(api_url, collection_id, data)

        elif data['type'] == "Feature":
            collection_id = data['collection']
            item_id = data['id']
            logger.info(f"Creating item {item_id} in collection {collection_id}")

            ## Handle case in which collection is not yet created for this item
            item_registered = create_item(api_url, collection_id, item_id, data)
            files_to_create.append(file_uri) if not item_registered else None

        ## Increment loop counter
        files_count+=1
            

    ## Update collections and items
    for file_uri in files_to_update:
        bucket, key = file_uri.replace("s3://","").split("/",1)
        data = client.get_object(Bucket=bucket, Key=key)
        data = json.loads(data['Body'].read())

        if data['type'] == "Collection":
            collection_id = data['id']
            logger.info(f"Updating collection {collection_id}")
            update_collection(api_url, collection_id, data)

        elif data['type'] == "Feature":
            collection_id = data['collection']
            item_id = data['id']
            logger.info(f"Updating item {item_id} in collection {collection_id}")
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
            logger.info("Waiting for message")
            msg = consumer.receive()
            interpret_message(msg.data(), api_url)
            consumer.acknowledge(msg)
    except pulsar.exceptions.Interrupted:
        pass
    except Exception as e:
        consumer.negative_acknowledge(msg)
    finally:
        consumer.close()
        client.close()


if __name__ == "__main__":
    cli(obj={})