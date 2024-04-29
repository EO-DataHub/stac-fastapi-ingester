import json
import logging
import os
import traceback
from http import HTTPStatus
from typing import Optional

import boto3
import botocore.exceptions
import click
import pulsar
import pulsar.exceptions
import requests

# configure boto3 logging
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("boto3").setLevel(logging.CRITICAL)

# create logger for stac fastapi ingester
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(filename="stac-fastapi-ingester.log", encoding="utf-8", level=logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


@click.group()
@click.argument("topic", type=str)
@click.pass_context
def cli(ctx, topic: str):
    ctx.ensure_object(dict)
    pulsar_url = os.getenv("PULSAR_URL", "")
    logger.info(pulsar_url)
    ctx.obj["CLIENT"] = pulsar.Client(pulsar_url)
    ctx.obj["TOPIC"] = topic
    logger.info(f"Connecting to broker '{pulsar_url}' with topic '{topic}'")


##############################
## DELETE FROM STAC FASTAPI ##
##############################


def delete_collection(api_url: str, collection_id: str):
    headers = {"accept": "application/json"}
    try:
        resp = requests.delete(
            f"{api_url}/collections/{collection_id}",
            headers=headers,
        )
        if resp.status_code == HTTPStatus.OK or resp.status_code == HTTPStatus.NO_CONTENT:
            logger.info("Status code: OK")
            logger.info(f"Deleted collection {collection_id}")
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            logger.warning("Status code: NOT_FOUND")
            logger.warning(f"Collection: {collection_id} does not exist.")
    except requests.ConnectionError as err:
        click.secho("failed to connect")
        logger.warning("failed to connect")
        logger.error(err)
        raise
    except Exception as err:
        logger.warning("Something went wrong")
        logger.debug(traceback.format_exc())
        logger.error(err)
        raise


def delete_item(api_url: str, collection_id: str, item_id: str):
    headers = {"accept": "application/json"}
    try:
        resp = requests.delete(
            f"{api_url}/collections/{collection_id}/items/{item_id}",
            headers=headers,
        )
        if resp.status_code == HTTPStatus.OK or resp.status_code == HTTPStatus.NO_CONTENT:
            logger.info("Status code: OK")
            logger.info(f"Deleted item {item_id}")
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            logger.warning("Status code: NOT_FOUND")
            logger.warning(f"Item: {item_id} in Collection: {collection_id} does not exist.")
    except requests.ConnectionError as err:
        logger.warning("failed to connect")
        logger.error(err)
        raise
    except Exception as err:
        logger.warning("Something went wrong")
        logger.debug(traceback.format_exc())
        logger.warning(err)
        raise


############################
## UPDATE IN STAC FASTAPI ##
############################


def update_collection(api_url: str, collection_id: str, data: dict):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.put(
            f"{api_url}/collections",
            headers=headers,
            json=data,
        )
        if resp.status_code == HTTPStatus.OK:
            logger.info("Status code: OK")
            logger.info(f"Updated Collection {collection_id}")
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            logger.warning("Status code: NOT_FOUND")
            logger.warning(f"Collection: {collection_id} not updated as doesn't exist.")
    except requests.ConnectionError as err:
        logger.warning("failed to connect")
        logger.error(err)
        raise
    except Exception as err:
        logger.warning("Something went wrong")
        logger.debug(traceback.format_exc())
        logger.warning(err)
        raise


def update_item(api_url: str, collection_id: str, item_id, data: dict):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.put(
            f"{api_url}/collections/{collection_id}/items/{item_id}",
            headers=headers,
            json=data,
        )
        if resp.status_code == HTTPStatus.OK:
            logger.info("Status code: OK")
            logger.info(f"Updated Item {item_id}")
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            logger.warning("Status code: NOT_FOUND")
            response_decoded = json.loads(resp.content.decode())
            response_decoded_description = response_decoded["description"]
            if "Item" in response_decoded_description:
                logger.warning(
                    f"Item: {item_id} in Collection: {collection_id} not updated as item "
                    "doesn't exist."
                )
            elif "Collection" in response_decoded_description:
                logger.warning(
                    f"Item: {item_id} in Collection: {collection_id} not updated as collection "
                    "doesn't exist."
                )
    except requests.ConnectionError as err:
        logger.warning("failed to connect")
        logger.error(err)
        raise
    except Exception as err:
        logger.warning("Something went wrong")
        logger.debug(traceback.format_exc())
        logger.warning(err)
        raise


############################
## CREATE IN STAC FASTAPI ##
############################


def create_collection(api_url: str, collection_id: str, data: dict):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            f"{api_url}/collections",
            headers=headers,
            json=data,
        )
        if resp.status_code == HTTPStatus.OK:
            logger.info("Status code: OK")
            logger.info(f"Created Collection {collection_id}")
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
            logger.warning(f"Collection: {collection_id} already exists")
    except requests.ConnectionError as err:
        logger.warning("failed to connect")
        logger.error(err)
        raise
    except Exception as err:
        logger.warning("Something went wrong")
        logger.debug(traceback.format_exc())
        logger.warning(err)
        raise


def create_item(api_url: str, collection_id: str, item_id: str, data: dict):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            f"{api_url}/collections/{collection_id}/items",
            headers=headers,
            json=data,
        )
        if resp.status_code == HTTPStatus.OK:
            logger.info("Status code: OK")
            logger.info(f"Created Item {item_id}")
            return True
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            # Add files awaiting collection creation to the end of the list again
            logger.warning(f"Collection: {collection_id} not yet created, will try again in a bit")
            return False
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
            logger.warning(f"Item: {item_id} in Collection: {collection_id} already exists")
            return True
    except requests.ConnectionError as err:
        logger.warning("failed to connect")
        logger.error(err)
        raise
    except Exception as err:
        logger.warning("Something went wrong")
        logger.debug(traceback.format_exc())
        logger.warning(err)
        raise


def load_data_from_s3(client: botocore.client, bucket_name: str, file_key: str) -> dict:
    try:
        data = client.get_object(Bucket=bucket_name, Key=file_key)
        data = json.loads(data["Body"].read())
        return data
    except botocore.exceptions.ParamValidationError:
        logger.warning("Provided bucket name or file key is not supported.")
        return False
    except Exception as err:
        logger.debug(traceback.format_exc())
        logger.warning(err)
        logger.error("Failed to load S3 object")
        raise


def interpret_message(msg: str, api_url: str):
    # Configure boto3 client ready for data access

    if os.getenv("AWS_ACCESS_KEY") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        session = boto3.session.Session(
            aws_access_key_id=os.environ["AWS_ACCESS_KEY"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
        client = session.client("s3")

    else:
        client = boto3.client("s3")

    # Extract as JSON dictionary
    updates_json = json.loads(msg)

    # Extract bucket name from message
    bucket_name = updates_json["bucket_name"]

    # Extract file names into actions lists
    files_to_update = updates_json["updated_keys"] if "updated_keys" in updates_json.keys() else []
    files_to_delete = updates_json["deleted_keys"] if "deleted_keys" in updates_json.keys() else []
    files_to_create = updates_json["added_keys"] if "added_keys" in updates_json.keys() else []

    # Delete items and collections
    for file_key in files_to_delete:
        # We can track deleted collections as this will also delete all associated items so no need
        # to call the delete items endpoint as well
        deleted_collections = set()

        data = load_data_from_s3(client, bucket_name, file_key)
        if not data:
            continue

        if data.get("type") == "Collection":
            collection_id = data["id"]
            logger.info(f"Deleting collection {collection_id}")
            deleted_collections.add(collection_id)
            delete_collection(api_url, collection_id)

        elif data.get("type") == "Feature":
            collection_id = data["collection"]
            if collection_id in deleted_collections:
                continue
            item_id = data["id"]
            logger.info(f"Deleting item {item_id} in collection {collection_id}")
            delete_item(api_url, collection_id, item_id)

    # Create new collections and items
    num_files_to_create = len(files_to_create)
    files_count = 0

    for file_key in files_to_create:
        # Variable to prevent endless looping, limits number of loops to at most 2
        if files_count >= num_files_to_create * 2:
            break

        data = load_data_from_s3(client, bucket_name, file_key)
        if not data:
            continue

        if data.get("type") == "Collection":
            collection_id = data["id"]
            logger.info(f"Creating collection {collection_id}")
            create_collection(api_url, collection_id, data)

        elif data.get("type") == "Feature":
            collection_id = data["collection"]
            item_id = data["id"]
            logger.info(f"Creating item {item_id} in collection {collection_id}")

            # Handle case in which collection is not yet created for this item
            item_registered = create_item(api_url, collection_id, item_id, data)
            files_to_create.append(file_key) if not item_registered else None

        # Increment loop counter
        files_count += 1

    # Update collections and items
    for file_key in files_to_update:
        data = load_data_from_s3(client, bucket_name, file_key)
        if not data:
            continue

        if data.get("type") == "Collection":
            collection_id = data["id"]
            logger.info(f"Updating collection {collection_id}")
            update_collection(api_url, collection_id, data)

        elif data.get("type") == "Feature":
            collection_id = data["collection"]
            item_id = data["id"]
            logger.info(f"Updating item {item_id} in collection {collection_id}")
            update_item(api_url, collection_id, item_id, data)


@cli.command()
@click.option("--prefix", type=str, default=None)
@click.pass_context
def subscribe(ctx, prefix: Optional[str] = None):
    """
    Subscribe to messages from a Pulsar broker.
    """

    client: pulsar.Client = ctx.obj["CLIENT"]
    topic: str = ctx.obj["TOPIC"]
    consumer = client.subscribe(topic=topic, subscription_name=prefix)
    api_url = os.getenv("FASTAPI_URL", "")
    try:
        while True:
            logger.info("Waiting for message")
            msg = consumer.receive()
            interpret_message(msg.data().decode("utf-8"), api_url)
            consumer.acknowledge(msg)
    except pulsar.exceptions.Interrupted:
        pass
    except Exception as err:
        logger.debug(traceback.format_exc())
        logger.error(err)
        consumer.negative_acknowledge(msg)
    finally:
        consumer.close()
        client.close()


if __name__ == "__main__":
    cli(obj={})
