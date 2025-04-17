import logging
from http import HTTPStatus

import requests


def log_response(
    resp: requests.models.Response,
    data_id: str,
    catalog_path: str,
    api_url: str,
    data_type: str,
):
    http_method = resp.request.method
    action = "Create" if http_method == "POST" else "Update"

    if resp.status_code == HTTPStatus.OK:
        logging.info(f"{action}d {data_type}: {data_id} at location {catalog_path}")
    elif resp.status_code == HTTPStatus.CONFLICT:
        logging.warning(
            f"CONFLICT: {data_type}: {data_id} already exists at location " f"{catalog_path}"
        )
    elif resp.status_code == HTTPStatus.NOT_FOUND:
        if http_method == "PUT":
            logging.warning(
                f"NOT_FOUND: {data_type}: {data_id} not {action}d as entry "
                f"at location {catalog_path} doesn't exist"
            )
        elif http_method == "POST":
            logging.warning(
                f"NOT_FOUND: {data_type}: {data_id} not {action}d at location "
                f"{catalog_path}, assume parent is missing"
            )
    else:
        logging.warning(f"{data_type}: {data_id} not {action}d at location {catalog_path}")
        logging.warning(f"Status Code: {resp.status_code} on url: {api_url}/{catalog_path}")
        logging.warning(f"Status message is {resp.content}")


def log_response_delete(
    resp: requests.models.Response,
    catalog_path: str,
    api_url: str,
):
    action = "Delete"

    if resp.status_code == HTTPStatus.NO_CONTENT:
        logging.info(f"{action}d entry at {catalog_path}")
    elif resp.status_code == HTTPStatus.NOT_FOUND:
        logging.warning(
            f"NOT_FOUND: Failed to {action} entry at {catalog_path} as it doesn't exist"
        )

    else:
        logging.warning(f"Entry at {catalog_path} not {action}d")
        logging.warning(f"Status Code: {resp.status_code} on url: {api_url}/{catalog_path}")
        logging.warning(f"Status message is {resp.content}")
