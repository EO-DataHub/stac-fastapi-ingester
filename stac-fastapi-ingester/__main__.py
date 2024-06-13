import json
import logging
import os
import time
import traceback
from http import HTTPStatus
from typing import Optional

import boto3
import botocore.client
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

# set the time converter to UTC
formatter.converter = time.gmtime

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


def delete_catalog(api_url: str, catalog_path: str):
    headers = {"accept": "application/json"}
    try:
        resp = requests.delete(
            f"{api_url}/catalogs/{catalog_path}",
            headers=headers,
        )
        if resp.status_code == HTTPStatus.OK or resp.status_code == HTTPStatus.NO_CONTENT:
            logger.info("Status code: OK")
            logger.info(f"Deleted Catalog {catalog_path}")
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            logger.warning("Status code: NOT_FOUND")
            logger.warning(f"Catalog: {catalog_path} does not exist.")
        else:
            logger.warning(f"Catalog: {catalog_path} not deleted")
            logger.warning(
                f"Status Code: {resp.status_code} on url: " f"{api_url}/catalogs/{catalog_path}"
            )
    except requests.ConnectionError as err:
        click.secho("failed to connect")
        logger.warning(f"Catalog: {catalog_path} not deleted")
        logger.error(err)
        raise
    except Exception as err:
        logger.warning(f"Catalog: {catalog_path} not deleted")
        logger.error(err)
        raise


def delete_collection(api_url: str, collection_id: str, catalog_path: str):
    headers = {"accept": "application/json"}
    try:
        resp = requests.delete(
            f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}",
            headers=headers,
        )
        if resp.status_code == HTTPStatus.OK or resp.status_code == HTTPStatus.NO_CONTENT:
            logger.info("Status code: OK")
            logger.info(f"Deleted Collection {collection_id}")
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            logger.warning("Status code: NOT_FOUND")
            logger.warning(
                f"Collection: {collection_id} in Catalog: {catalog_path} does not " "exist."
            )
        else:
            logger.warning(f"Collection: {collection_id} in Catalog: {catalog_path} not updated")
            logger.warning(
                f"Status Code: {resp.status_code} on url: "
                f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}"
            )
    except requests.ConnectionError as err:
        click.secho("Failed to connect")
        logger.warning(f"Collection: {collection_id} not deleted")
        logger.error(err)
        raise
    except Exception as err:
        logger.warning(f"Collection: {collection_id} not deleted")
        logger.error(err)
        raise


def delete_item(api_url: str, collection_id: str, item_id: str, catalog_path: str):
    headers = {"accept": "application/json"}
    try:
        resp = requests.delete(
            f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{item_id}",
            headers=headers,
        )
        if resp.status_code == HTTPStatus.OK or resp.status_code == HTTPStatus.NO_CONTENT:
            logger.info("Status code: OK")
            logger.info(f"Deleted Item {item_id}")
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            logger.warning("Status code: NOT_FOUND")
            logger.warning(
                f"Item: {item_id} in Collection: {collection_id} in Catalog: {catalog_path} does "
                "not exist."
            )
        else:
            logger.warning(
                f"Item: {item_id} in Collection: {collection_id} in Catalog: {catalog_path} not updated"
            )
            logger.warning(
                f"Status Code: {resp.status_code} on url: "
                f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/"
                f"items/{item_id}"
            )
    except Exception as err:
        logger.warning(f"Item: {item_id} not deleted")
        logger.error(err)
        raise


############################
## UPDATE IN STAC FASTAPI ##
############################


def update_catalog(api_url: str, data: dict, catalog_path: str):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.put(
            f"{api_url}/catalogs/{catalog_path}",
            headers=headers,
            json=data,
        )
        if resp.status_code == HTTPStatus.OK:
            logger.info("Status code: OK")
            logger.info(f"Updated Catalog {catalog_path}")
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            logger.warning("Status code: NOT_FOUND")
            logger.warning(f"Catalog: {catalog_path} not updated as doesn't exist.")
        else:
            logger.warning(f"Catalog: {catalog_path} not updated")
            logger.warning(
                f"Status Code: {resp.status_code} on url: {api_url}/catalogs/{catalog_path}"
            )
            logger.warning("data is")
            logger.warning(data)
    except Exception as err:
        logger.warning(f"Catalog: {catalog_path} not updated")
        logger.error(err)
        raise


def update_collection(api_url: str, collection_id: str, data: dict, catalog_path: str) -> bool:
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.put(
            f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}",
            headers=headers,
            json=data,
        )
        if resp.status_code == HTTPStatus.OK:
            logger.info("Status code: OK")
            logger.info(
                f"Updated Collection {collection_id} in Catalog {catalog_path}/{collection_id}"
            )
            return True
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
            return True
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            logger.warning("Status code: NOT_FOUND")
            logger.warning(
                f"Collection: {collection_id} not updated as doesn't exist in Catalog "
                f"{catalog_path}."
            )
            return False
        else:
            logger.warning(f"Collection: {collection_id} in Catalog: {catalog_path} not updated")
            logger.warning(
                f"Status Code: {resp.status_code} on url: "
                f"{api_url}/catalogs/{catalog_path}/collections"
            )
            logger.warning("data is")
            logger.warning(data)
            # return but don't try again
            return True
    except Exception as err:
        logger.warning(f"Collection: {collection_id} not updated")
        logger.error(err)
        raise


def update_item(api_url: str, collection_id: str, item_id, data: dict, catalog_path: str) -> bool:
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.put(
            f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{item_id}",
            headers=headers,
            json=data,
        )
        if resp.status_code == HTTPStatus.OK:
            logger.info("Status code: OK")
            logger.info(f"Updated Item {item_id}")
            return True
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
            return True
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            logger.warning("Status code: NOT_FOUND")
            response_decoded = json.loads(resp.content.decode())
            response_decoded_description = response_decoded["description"]
            if "Item" in response_decoded_description:
                logger.warning(
                    f"Item: {item_id} in Collection: {collection_id} in Catalog: {catalog_path} not "
                    "updated as item doesn't exist."
                )
            elif "Collection" in response_decoded_description:
                logger.warning(
                    f"Item: {item_id} in Collection: {collection_id} in Catalog: {catalog_path} not "
                    "updated as collection doesn't exist."
                )
            elif "Catalog" in response_decoded_description:
                logger.warning(
                    f"Item: {item_id} in Collection: {collection_id} in Catalog: {catalog_path} not "
                    "updated as catalog doesn't exist."
                )
            return False
        else:
            logger.warning(
                f"Item: {item_id} in Collection: {collection_id} in Catalog: {catalog_path} not updated"
            )
            logger.warning(
                f"Status Code: {resp.status_code} on url: "
                f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/"
                f"items/{item_id}"
            )
            logger.warning("data is")
            logger.warning(data)
            # return but don't try again
            return True
    except Exception as err:
        logger.warning(f"Item: {item_id} not updated")
        logger.error(err)
        raise


############################
## CREATE IN STAC FASTAPI ##
############################


def create_catalog(api_url: str, data: dict, catalog_path: Optional[str]):
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        if catalog_path:
            catalog_path = f"/{catalog_path}"
        else:
            # If no catalog path is provided, this is a top level catalog
            catalog_path = ""
        resp = requests.post(
            f"{api_url}/catalogs{catalog_path}",
            headers=headers,
            json=data,
        )
        if resp.status_code == HTTPStatus.OK:
            logger.info("Status code: OK")
            logger.info(f"Created Catalog {catalog_path}")
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
            logger.warning(f"Catalog: {catalog_path} already exists")
        else:
            logger.warning(f"Catalog: {catalog_path} not created")
            logger.warning(f"Status Code: {resp.status_code} on url: {api_url}/catalogs")
            logger.warning("data is")
            logger.warning(data)
    except Exception as err:
        logger.warning(f"Catalog: {catalog_path} not created")
        logger.error(err)
        raise


def create_collection(api_url: str, collection_id: str, data: dict, catalog_path: str) -> bool:
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            f"{api_url}/catalogs/{catalog_path}/collections",
            headers=headers,
            json=data,
        )
        if resp.status_code == HTTPStatus.OK:
            logger.info("Status code: OK")
            logger.info(f"Created Collection {collection_id}")
            return True
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            # Add files awaiting catalog creation to the end of the list again
            logger.warning(f"Catalog: {catalog_path} not yet created, will try again in a bit")
            return False
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
            logger.warning(f"Collection: {collection_id} in Catalog: {catalog_path} already exists")
            return True
        else:
            logger.warning(f"Collection: {collection_id} in Catalog: {catalog_path} not created")
            logger.warning(
                f"Status Code: {resp.status_code} on url: {api_url}/catalogs/{catalog_path}/collections"
            )
            logger.warning("data is")
            logger.warning(data)
            # return but don't try again
            return True
    except Exception as err:
        logger.warning(f"Collection: {collection_id} not created")
        logger.error(err)
        raise


def create_item(
    api_url: str, collection_id: str, item_id: str, data: dict, catalog_path: str
) -> bool:
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items",
            headers=headers,
            json=data,
        )
        if resp.status_code == HTTPStatus.OK:
            logger.info("Status code: OK")
            logger.info(f"Created Item {item_id}")
            return True
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            # Add files awaiting catalog/collection creation to the end of the list again
            logger.warning(
                f"Collection: {collection_id} or Catalog: {catalog_path} not yet created, will "
                "try again in a bit"
            )
            return False
        elif resp.status_code == HTTPStatus.CONFLICT:
            logger.warning("Status code: CONFLICT")
            logger.warning(
                f"Item: {item_id} in Collection: {collection_id} in Catalog: {catalog_path} "
                "already exists"
            )
            return True
        else:
            logger.warning(
                f"Item: {item_id} in Collection: {collection_id} in Catalog: {catalog_path} not created"
            )
            logger.warning(
                f"Status Code: {resp.status_code} on url: {api_url}/catalogs/{catalog_path}/"
                f"collections/{collection_id}/items"
            )
            logger.warning("data is")
            logger.warning(data)
            # return but don't try again
            return True
    except Exception as err:
        logger.warning(f"Item: {item_id} not created")
        logger.error(err)
        raise


def load_data_from_s3(client: botocore.client, bucket_name: str, file_key: str) -> dict:
    try:
        data = client.get_object(Bucket=bucket_name, Key=file_key)
        data = json.loads(data["Body"].read())
        return data
    except botocore.exceptions.ParamValidationError:
        logger.warning("Provided bucket name or file key is not supported.")
        return False
    except json.decoder.JSONDecodeError:
        # File is not json so ignore this file
        logger.warning(f"File {file_key} is not a JSON file. Ignoring.")
        return False
    except UnicodeDecodeError:
        # File is not json so ignore this file
        logger.warning(f"File {file_key} is not a JSON file. Ignoring.")
        return False
    except client.exceptions.NoSuchKey:
        # File key does not exist
        logger.warning(f"File {file_key} does not exist in S3. Ignoring.")
        return False
    except Exception as err:
        logger.error(err)
        logger.error(f"Failed to load S3 object with key: {file_key}")
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

    # Delete catalogs, collections and items
    for file_key in files_to_delete:
        # We can track deleted collections as this will also delete all associated items so no need
        # to call the delete items endpoint as well
        deleted_collections = set()

        data = load_data_from_s3(client, bucket_name, file_key)
        if not data:
            continue

        # Extract catalog path for this file
        catalog_path_list = file_key.split("/")
        catalog_path_list = catalog_path_list[:-1]
        # Remove first key in catalog path (expected to be "transformed")
        if len(catalog_path_list) == 1:
            # If only one directory provided, no parent catalog is available
            catalog_path = ""
        else:
            catalog_path_list = catalog_path_list[1:]
            catalog_path = "/".join(catalog_path_list)

        if data.get("type") == "Collection":
            collection_id = data["id"]
            logger.info(f"Deleting collection {collection_id}")
            deleted_collections.add(collection_id)
            delete_collection(api_url, collection_id, catalog_path)

        elif data.get("type") == "Feature":
            item_id = data["id"]
            if catalog_path == "":
                logger.warning(
                    f"Cannot delete Item {item_id} without catalog being specified, skipping."
                )
                continue
            # For items, we need to cut down the catalog path ignoring the 'collection' directory
            # Expected format is 'catalog/collection/item', we only need 'catalog'
            catalog_path_list = catalog_path.split("/")
            catalog_path = catalog_path_list[:-1]  # Remove 'collection' directory
            catalog_path = "/".join(catalog_path)
            collection_id = data["collection"]
            if collection_id in deleted_collections:
                continue
            logger.info(f"Deleting item {item_id} in collection {collection_id}")
            delete_item(api_url, collection_id, item_id, catalog_path)

        elif data.get("type") == "Catalog":
            logger.info(f"Deleting Catalog {catalog_path}")
            delete_catalog(api_url, catalog_path)

    # Create new catalogs, collections and items
    num_files_to_create = len(files_to_create)
    limit = num_files_to_create * 3
    files_count = 0

    for file_key in files_to_create:
        # Variable to prevent endless looping, limits number of loops to at most 3 to allow
        # catalogs and collections to be created
        if files_count >= limit:
            break

        data = load_data_from_s3(client, bucket_name, file_key)
        if not data:
            continue

        # Extract catalog path for this file
        catalog_path_list = file_key.split("/")
        catalog_path_list = catalog_path_list[:-1]
        # Remove first key in catalog path (expected to be "transformed")
        if len(catalog_path_list) == 1:
            # If only one directory provided, no parent catalog is available
            catalog_path = ""
        else:
            catalog_path_list = catalog_path_list[1:]
            catalog_path = "/".join(catalog_path_list)

        if data.get("type") == "Collection":
            collection_id = data["id"]
            logger.info(f"Creating Collection {collection_id} in catalog {catalog_path}")

            # Handle case in which catalog is not yet created for this collection
            item_registered = create_collection(api_url, collection_id, data, catalog_path)
            files_to_create.append(file_key) if not item_registered else None

        elif data.get("type") == "Feature":
            item_id = data["id"]
            if catalog_path == "":
                logger.warning(
                    f"Cannot create Item {item_id} without catalog being specified, skipping."
                )
                continue
            # For items, we need to cut down the catalog path ignoring the 'collection' directory
            # Expected format is 'catalog/collection/item', we only need 'catalog'
            catalog_path_list = catalog_path.split("/")
            catalog_path = catalog_path_list[:-1]  # Remove 'collection' directory
            catalog_path = "/".join(catalog_path)
            collection_id = data["collection"]
            logger.info(
                f"Creating Item {item_id} in collection {collection_id} in catalog {catalog_path}"
            )

            # Handle case in which catalog and/or collection is not yet created for this item
            item_registered = create_item(api_url, collection_id, item_id, data, catalog_path)
            files_to_create.append(file_key) if not item_registered else None

        elif data.get("type") == "Catalog":
            if catalog_path:
                logger.info(f"Creating Catalog {data['id']} in catalog {catalog_path}")
            else:
                logger.info(f"Creating a new base catalog, {data['id']}")
            create_catalog(api_url, data, catalog_path)

        # Increment loop counter
        files_count += 1

    # Update catalogs, collections and items
    num_files_to_update = len(files_to_update)
    limit = num_files_to_update * 3
    files_count = 0

    for file_key in files_to_update:
        # Variable to prevent endless looping, limits number of loops to at most 3 to allow
        # catalogs and collections to be created
        if files_count >= limit:
            break

        data = load_data_from_s3(client, bucket_name, file_key)
        if not data:
            continue

        # Extract catalog path for this file
        catalog_path_list = file_key.split("/")
        catalog_path_list = catalog_path_list[:-1]
        # Remove first key in catalog path (expected to be "transformed")
        if len(catalog_path_list) == 1:
            # If only one directory provided, no parent catalog is available
            catalog_path = ""
        else:
            catalog_path_list = catalog_path_list[1:]
            catalog_path = "/".join(catalog_path_list)

        if data.get("type") == "Collection":
            collection_id = data["id"]
            logger.info(f"Updating Collection {collection_id} in Catalog {catalog_path}")

            # Handle case in which catalog is not yet updated/created for this collection
            collection_updated = update_collection(api_url, collection_id, data, catalog_path)
            files_to_update.append(file_key) if not collection_updated else None

        elif data.get("type") == "Feature":
            item_id = data["id"]
            if catalog_path == "":
                logger.warning(
                    f"Cannot update Item {item_id} without catalog being specified, skipping."
                )
                continue
            # For items, we need to cut down the catalog path ignoring the 'collection' directory
            # Expected format is 'catalog/collection/item', we only need 'catalog'
            catalog_path_list = catalog_path.split("/")
            catalog_path = catalog_path_list[:-1]  # Remove 'collection' directory
            catalog_path = "/".join(catalog_path)
            collection_id = data["collection"]
            logger.info(
                f"Updating Item {item_id} in Collection {collection_id} in Catalog {catalog_path}"
            )

            # Handle case in which catalog and/or collection is not yet updated/created for this item
            item_updated = update_item(api_url, collection_id, item_id, data, catalog_path)
            files_to_update.append(file_key) if not item_updated else None

        elif data.get("type") == "Catalog":
            logger.info(f"Updating Catalog {catalog_path}")
            update_catalog(api_url, data, catalog_path)

        # Increment loop counter
        files_count += 1


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
            consumer.acknowledge(msg)
            logger.info(msg.data())
            interpret_message(msg.data().decode("utf-8"), api_url)
            consumer.acknowledge(msg)
            # Clear open catalogs dictionary cache
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
