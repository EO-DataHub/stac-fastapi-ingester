import json
import logging
from http import HTTPStatus

import requests

from .errors import InvalidSTACException, MissingParentError, SFAPIConnectionError
from .logs import log_response, log_response_delete


def create_or_update_entry(api_url: str, data: dict, workspace: str, catalog_path: str) -> None:
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    query_params = {"workspace": workspace}
    data_type = data.get("type")
    if not data_type:
        raise InvalidSTACException(f"STAC entry at {catalog_path} is missing a 'type' field")
    if data_type not in ["Catalog", "Collection", "Feature"]:
        raise InvalidSTACException(f"STAC entry at {catalog_path} has invalid 'type' field: {data_type}")
    entry_id = data.get("id")
    if not entry_id:
        raise InvalidSTACException(f"STAC entry at {catalog_path} is missing an 'id' field")

    logging.info(f"Creating/updating {data_type} {entry_id} in location {catalog_path}")

    try:
        resp = requests.put(
            f"{api_url}/{catalog_path}",
            headers=headers,
            json=data,
            params=query_params,
        )
        log_response(resp, entry_id, catalog_path, api_url, data_type)

        if resp.status_code == HTTPStatus.NOT_FOUND:
            # Remove file name from path
            new_path = catalog_path.rsplit("/", 1)[0]
            resp = requests.post(
                f"{api_url}/{new_path}",
                headers=headers,
                json=data,
                params=query_params,
            )

            log_response(resp, entry_id, new_path, api_url, data_type)

            if resp.status_code == HTTPStatus.NOT_FOUND:
                # raise temporary error to make sure the message is retried,
                # in case parent was missing
                raise MissingParentError()

        resp.raise_for_status()
    except requests.ConnectionError as err:
        logging.warning(f"Data: {catalog_path} not created/updated")
        logging.error(err)
        raise SFAPIConnectionError("Failed to connect to STAC-FastApi Service, retrying.") from err


def delete_entry(api_url: str, workspace: str, catalog_path: str) -> None:
    headers = {"accept": "application/json"}
    query_params = {"workspace": workspace}
    try:
        resp = requests.delete(
            f"{api_url}/{catalog_path}",
            headers=headers,
            params=query_params,
        )
        log_response_delete(resp, catalog_path, api_url)
        resp.raise_for_status()
    except requests.ConnectionError as err:
        logging.warning(f"Data: {catalog_path} not deleted")
        logging.error(err)
        raise SFAPIConnectionError("Failed to connect to STAC-FastApi Service, retrying.") from err


def update_entry_access_policy(
    api_url: str,
    policy: dict,
    workspace: str,
) -> None:

    # Parse policy details
    path = policy["path"]
    access_policy = policy["access"]

    headers = {"accept": "application/json", "Content-Type": "application/json"}
    query_params = {"workspace": workspace}

    try:
        resp = requests.put(
            f"{api_url}/{path}/access-policy",
            headers=headers,
            params=query_params,
            data=json.dumps(access_policy),
        )

        logging.info(f"Sent request to {api_url}/{path}/access-policy with inputs {access_policy}")

        if resp.status_code == HTTPStatus.NO_CONTENT:
            logging.info(f"Updated access control for data at {path}")
        elif resp.status_code == HTTPStatus.NOT_FOUND:
            logging.warning(
                f"Failed to update access control for data at {path} as catalog or collection does not exist"
            )
        else:
            logging.error(
                f"Failed to update access control for data at {path}, Status Code: "
                f"{resp.status_code} on url: {api_url}/{path} with inputs "
                f"{access_policy} with message {resp.content}"
            )
    except requests.ConnectionError as err:
        logging.warning(f"Access Policy: {path} not updated")
        logging.error(err)
        raise SFAPIConnectionError("Failed to connect to STAC-FastApi Service, retrying.") from err


def handle_access_policy(api_url: str, data: dict, workspace: str) -> None:
    access_policies = data["policies"]
    # Sort by hierarchy level to ensure that parent catalogs are handled
    # before subcatalogs and collections
    access_policies.sort(key=lambda p: p["path"].count("/"))
    for policy in access_policies:
        logging.info("Updating access policy for %s in workspace %s", policy.get("path", ""), workspace)
        update_entry_access_policy(api_url, policy, workspace)
