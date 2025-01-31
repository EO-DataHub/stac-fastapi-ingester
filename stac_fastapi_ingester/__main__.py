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

MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))


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


############################
## UPDATE ACCESS POLICIES ##
############################


def update_access_policy(
    api_url: str,
    policy: dict,
    workspace: str,
) -> bool:

    # Parse policy details
    path = policy["path"]
    access_policy = policy["access"]

    headers = {"accept": "application/json", "Content-Type": "application/json"}
    query_params = {"workspace": workspace}

    resp = requests.put(
        f"{api_url}/catalogs/{path}/access-policy",
        headers=headers,
        params=query_params,
        data=json.dumps(access_policy),
    )

    logger.info(
        f"Sent request to {api_url}/catalogs/{path}/access-policy with inputs {access_policy}"
    )

    if resp.status_code == HTTPStatus.NO_CONTENT:
        logger.info(f"Updated access control for data at {path}")
    elif resp.status_code == HTTPStatus.NOT_FOUND:
        logger.warning(
            f"Failed to update access control for data at {path} as catalog or collection does not exist"
        )
        return False
    else:
        logger.error(
            f"Failed to update access control for data at {path}, Status Code: "
            f"{resp.status_code} on url: {api_url}/catalogs/{path} with inputs "
            f"{access_policy} with message {resp.content}"
        )
    return True


def handle_access_policy(data: dict, api_url: str, workspace: str):
    access_policies = data["policies"]
    # Sort by hierarchy level to ensure that parent catalogs are handle
    # before subcatalogs and collections
    access_policies.sort(key=lambda p: p["path"].count("/"))
    for policy in access_policies:
        # TODO: Add support for "group-lists" if required
        # Construct STAC-FastApi request to update policy
        update_access_policy(api_url, policy, workspace)


##############################
## DELETE FROM STAC FASTAPI ##
##############################


def delete_catalog(api_url: str, workspace: str, catalog_path: str, catalog_id: str):
    headers = {"accept": "application/json"}
    query_params = {"workspace": workspace}
    data_type = "Catalogue"
    # Handle top-level catalog
    if catalog_path:
        gen_catalog_path = catalog_path.replace("/", "/catalogs/")
        combined_url = f"{api_url}/catalogs/{gen_catalog_path}/catalogs/{catalog_id}"
    else:
        combined_url = f"{api_url}/catalogs/root/catalogs/{catalog_id}"

    try:
        resp = requests.delete(
            combined_url,
            headers=headers,
            params=query_params,
        )

        log_response(resp, None, catalog_id, catalog_path, api_url, data_type)

    except requests.ConnectionError as err:
        click.secho("failed to connect")
        logger.warning(
            f"Catalog: {catalog_id} not deleted"
            f"from {catalog_path if catalog_path else 'top-level'}"
        )
        logger.error(err)
    except Exception as err:
        logger.warning(
            f"Catalog: {catalog_id} not deleted "
            f"{f'from {catalog_path}' if catalog_path else 'from top-level'}"
        )
        logger.error(err)


def delete_collection(api_url: str, collection_id: str, workspace: str, catalog_path: str):
    headers = {"accept": "application/json"}
    query_params = {"workspace": workspace}
    data_type = "Collection"
    try:
        gen_catalog_path = catalog_path.replace("/", "/catalogs/")
        resp = requests.delete(
            f"{api_url}/catalogs/{gen_catalog_path}/collections/{collection_id}",
            headers=headers,
            params=query_params,
        )
        log_response(resp, None, collection_id, catalog_path, api_url, data_type)

    except requests.ConnectionError as err:
        click.secho("Failed to connect")
        logger.warning(f"Collection: {collection_id} not deleted")
        logger.error(err)
    except Exception as err:
        logger.warning(f"Collection: {collection_id} not deleted")
        logger.error(err)


def delete_item(api_url: str, collection_id: str, item_id: str, workspace: str, catalog_path: str):
    headers = {"accept": "application/json"}
    query_params = {"workspace": workspace}
    data_type = "Item"
    try:
        gen_catalog_path = catalog_path.replace("/", "/catalogs/")
        resp = requests.delete(
            f"{api_url}/catalogs/{gen_catalog_path}/collections/{collection_id}/items/{item_id}",
            headers=headers,
            params=query_params,
        )
        log_response(resp, None, item_id, catalog_path, api_url, data_type)

    except Exception as err:
        logger.warning(
            f"Item: {item_id} in Collection: {collection_id} in Catalog: {catalog_path} not deleted"
        )
        logger.error(err)


######################################
## CREATE OR UPDATE IN STAC FASTAPI ##
######################################


def log_response(
    resp: requests.models.Response,
    data: dict,
    data_id: str,
    catalog_path: str,
    api_url: str,
    item_type: str,
):
    http_method = resp.request.method
    action = (
        "delete" if http_method == "DELETE" else "create" if http_method == "POST" else "update"
    )

    if resp.status_code == HTTPStatus.OK:
        logger.info("Status Code: OK")
        logger.info(
            f"{action}d {item_type} {data_id} in {catalog_path if catalog_path else 'top-level'} catalog"
        )
    elif resp.status_code == HTTPStatus.CONFLICT:
        logger.warning("Status Code: CONFLICT")
        logger.warning(
            f"{item_type}: {data_id} already exists in "
            f"{catalog_path if catalog_path else 'top-level'} catalog"
        )
    elif resp.status_code == HTTPStatus.NOT_FOUND:
        logger.warning("Status Code: NOT_FOUND")
        if http_method == "PUT":
            logger.warning(
                f"{item_type}: {data_id} not {action}d as item {data_id} "
                f"or collection {catalog_path} doesn't exist"
            )
        elif http_method == "POST":
            logger.warning(
                f"{item_type}: {data_id} not {action}d as catalog or collection {catalog_path} doesn't exist"
            )
    else:
        logger.warning(f"{item_type}: {data_id} not {action}d in {catalog_path}")
        logger.warning(f"Status Code: {resp.status_code} on url: {api_url}/catalogs")
        logger.warning(f"Status message is {resp.content}")
        logger.warning("data is")
        logger.warning(data)


def create_or_update_catalog(
    api_url: str,
    data: dict,
    workspace: str,
    catalog_path: Optional[str] = None,
    catalog_id: Optional[str] = None,
) -> bool:
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    query_params = {"workspace": workspace}
    data_type = "Catalogue"
    catalogue_exists = True
    try:

        if catalog_id:
            if catalog_path:
                gen_catalog_path = catalog_path.replace("/", "/catalogs/")
                combined_url = f"{api_url}/catalogs/{gen_catalog_path}/catalogs/{catalog_id}"
            else:
                combined_url = f"{api_url}/catalogs/root/catalogs/{catalog_id}"

            logging.info(f"Attempting to update {combined_url}")
            resp = requests.put(
                combined_url,
                headers=headers,
                json=data,
                params=query_params,
            )

            log_response(resp, data, data["id"], catalog_path, api_url, data_type)

        else:
            catalogue_exists = False

        if not catalogue_exists or resp.status_code == HTTPStatus.NOT_FOUND:
            if catalog_path:
                gen_catalog_path = catalog_path.replace("/", "/catalogs/")
                combined_url = f"{api_url}/catalogs/{gen_catalog_path}/catalogs"
            else:
                # If no catalog path is provided, this is a top level catalog
                combined_url = f"{api_url}/catalogs/root/catalogs"
            logging.info(f"Attempting to add {combined_url}")
            resp = requests.post(
                combined_url,
                headers=headers,
                json=data,
                params=query_params,
            )

            log_response(resp, data, data["id"], catalog_path, api_url, data_type)

        resp.raise_for_status()

        return True

    except Exception as err:
        logger.error(
            f"Catalog: {data['id']} not created or updated "
            f"{f'in {catalog_path}' if catalog_path else 'at top-level'}"
        )
        logger.error(err)
        return True


def create_or_update_collection(
    api_url: str, collection_id: str, data: dict, workspace: str, catalog_path: str
) -> bool:
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    query_params = {"workspace": workspace}
    data_type = "Collection"
    try:
        gen_catalog_path = catalog_path.replace("/", "/catalogs/")
        resp = requests.put(
            f"{api_url}/catalogs/{gen_catalog_path}/collections/{collection_id}",
            headers=headers,
            json=data,
            params=query_params,
        )

        log_response(resp, data, collection_id, catalog_path, api_url, data_type)

        if resp.status_code == HTTPStatus.NOT_FOUND:

            resp = requests.post(
                f"{api_url}/catalogs/{gen_catalog_path}/collections",
                # change to `collections` after updating ADES endpoint
                headers=headers,
                json=data,
                params=query_params,
            )

            log_response(resp, data, collection_id, catalog_path, api_url, data_type)
        resp.raise_for_status()

        return True

    except Exception as err:
        logger.error(
            f"Collection: {collection_id} in Catalog: "
            f"{f'{catalog_path}' if catalog_path else 'at top-level'} "
            f"not created or updated"
        )
        logger.error(err)
        return False


def create_or_update_item(
    api_url: str, collection_id: str, item_id: str, data: dict, workspace: str, catalog_path: str
) -> bool:
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    query_params = {"workspace": workspace}
    data_type = "Item"
    try:
        gen_catalog_path = catalog_path.replace("/", "/catalogs/")
        resp = requests.put(
            f"{api_url}/catalogs/{gen_catalog_path}/collections/{collection_id}/items/{item_id}",
            headers=headers,
            json=data,
            params=query_params,
        )
        log_response(resp, data, item_id, catalog_path, api_url, data_type)

        if resp.status_code == HTTPStatus.NOT_FOUND:
            resp = requests.post(
                f"{api_url}/catalogs/{gen_catalog_path}/collections/{collection_id}/items",
                headers=headers,
                json=data,
                params=query_params,
            )

            log_response(resp, data, item_id, catalog_path, api_url, data_type)
        resp.raise_for_status()

        return True

    except Exception as err:
        logger.error(
            f"Item: {item_id} in Collection: {collection_id} in "
            f"Catalog: {catalog_path} not created or updated"
        )
        logger.error(err)
        return False


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
    except botocore.exceptions.ClientError as err:
        if err.response["Error"]["Code"] == "NoSuchKey":
            # File key does not exist
            logger.warning(f"File {file_key} does not exist in S3. Ignoring.")
            return False
        else:
            logger.error(err)
            logger.error(f"Failed to load S3 object with key: {file_key}")
            return False
    except Exception as err:
        logger.error(err)
        logger.error(f"Failed to load S3 object with key: {file_key}")
        return False


def make_retry_message(original_message: dict, files_to_retry: list) -> dict:
    message = original_message.copy()
    message["updated_keys"] = files_to_retry
    message["added_keys"] = []
    message["deleted_keys"] = []
    message["retries"] = int(message.get("retries", 0)) + 1
    return message


def interpret_message(msg: str, api_url: str) -> Optional[dict]:
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

    # Extract workspace from message
    workspace = updates_json["workspace"]

    # Extract number of retry attempts, if any:
    retry_count = updates_json.get("retries", 0)

    # Extract file names into actions lists
    files_to_update = updates_json["updated_keys"] if "updated_keys" in updates_json.keys() else []
    files_to_delete = updates_json["deleted_keys"] if "deleted_keys" in updates_json.keys() else []
    files_to_create = updates_json["added_keys"] if "added_keys" in updates_json.keys() else []
    files_to_create_or_update = files_to_create + files_to_update

    # Data counts for logging
    num_deleted = len(files_to_delete)
    num_created_or_updated = len(files_to_create_or_update)

    # Sort by key length to ensure that catalogs are created before collections before items
    files_to_create_or_update.sort(key=lambda s: s.count("/"))

    files_to_retry = []

    # Delete catalogs, collections and items
    for count, file_key in enumerate(files_to_delete):
        logger.info("Processing %s, %i of %i in list of deleted keys", file_key, count, num_deleted)

        data = load_data_from_s3(client, bucket_name, file_key)
        if not data:
            continue

        # Extract catalog path for this file
        catalog_path_list = file_key.split("/")
        catalog_path_list = catalog_path_list[:-1]

        # TODO: In future we can use:
        # file_id = catalog_path_list[-1] to extract current file name (doesn't work for collections)

        # Remove first key in catalog path (expected to be "transformed")
        if len(catalog_path_list) == 1:
            # If only one directory provided, no parent catalog is available
            catalog_path = ""
        else:
            catalog_path_list = catalog_path_list[1:]
            catalog_path = "/".join(catalog_path_list)

        if data.get("type") == "Collection":
            collection_id = data["id"]
            logger.info(
                f"Deleting collection {collection_id} from "
                f"Catalog {catalog_path if catalog_path else 'top-level'}"
            )
            delete_collection(api_url, collection_id, workspace, catalog_path)

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
            try:
                collection_id = data["collection"]
            except KeyError:
                logging.error(f"Key 'collection' not found in file {file_key}")
                continue
            logger.info(
                f"Deleting item {item_id} in collection {collection_id} in "
                f"Catalog {catalog_path if catalog_path else 'top-level'}"
            )
            delete_item(api_url, collection_id, item_id, workspace, catalog_path)

        elif data.get("type") == "Catalog":
            # TODO: update this to read from file key rather than the STAC file itself,
            # currently left as is for consistency
            catalog_id = data["id"]
            logger.info(
                f"Deleting Catalog {catalog_id} from Catalog {catalog_path if catalog_path else 'top-level'}"
            )
            delete_catalog(api_url, workspace, catalog_path, catalog_id)

    for count, file_key in enumerate(files_to_create_or_update):
        logger.info(
            "Processing %s, %i of %i in list of created and updated keys",
            file_key,
            count,
            num_created_or_updated,
        )

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

        if file_key.endswith("meta_access_policy.json"):
            logger.info("Creating access policy for workspace %s", workspace)
            handle_access_policy(data, api_url, workspace)
            continue

        if data.get("type") == "Collection":
            collection_id = data["id"]
            logger.info(f"Creating/updating Collection {collection_id} in catalog {catalog_path}")

            # Handle case in which catalog is not yet created for this collection
            success = create_or_update_collection(
                api_url, collection_id, data, workspace, catalog_path
            )
            if not success:
                files_to_retry.append(file_key)

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
            try:
                collection_id = data["collection"]
            except KeyError:
                logging.error(f"Key 'collection' not found in file {file_key}")
                continue
            logger.info(
                f"Creating/updating Item {item_id} in collection {collection_id} in catalog {catalog_path}"
            )

            # Handle case in which catalog and/or collection is not yet created for this item
            success = create_or_update_item(
                api_url, collection_id, item_id, data, workspace, catalog_path
            )

            if not success:
                files_to_retry.append(file_key)

        elif data.get("type") == "Catalog":
            logger.info(
                f"Creating/updating Catalog {data['id']} in Catalog"
                f" {catalog_path if catalog_path else 'top-level'}"
            )
            success = create_or_update_catalog(api_url, data, workspace, catalog_path, data["id"])

            if not success:
                files_to_retry.append(file_key)

    if files_to_retry and retry_count < MAX_RETRIES:
        logger.warning(
            f"Retries required for {files_to_retry}. {retry_count} attempts currently made"
        )
        retry_message = make_retry_message(updates_json, files_to_retry)

        return retry_message


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
    producer = client.create_producer(
        topic=topic,
        producer_name=prefix,
        chunking_enabled=True,
    )
    api_url = os.getenv("FASTAPI_URL", "")
    try:
        while True:
            logger.info("Waiting for message")
            msg = consumer.receive()
            logger.info(msg.data())
            retry_message = interpret_message(msg.data().decode("utf-8"), api_url)

            if retry_message:
                logger.info(f"Retry {retry_message['retries']}: {retry_message}")
                producer.send(json.dumps(retry_message).encode("utf-8"))

            consumer.acknowledge(msg)
    except pulsar.exceptions.Interrupted:
        pass
    except Exception as err:
        logger.info(traceback.format_exc())
        logger.error(err)
        consumer.negative_acknowledge(msg)
    finally:
        consumer.close()
        client.close()


if __name__ == "__main__":
    cli(obj={})
