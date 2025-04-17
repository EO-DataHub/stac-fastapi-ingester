import logging
from unittest import mock

import pytest

from stac_fastapi_ingester.logs import log_response, log_response_delete


@pytest.mark.parametrize(
    "req_method, status_code, response_json, expected_exception",
    [
        (
            "POST",
            200,
            {"message": "Entry Created Successfully"},
            "Created Catalog: catalog_id at location test/path",
        ),
        (
            "POST",
            404,
            {"message": "Not Found"},
            "NOT_FOUND: Catalog: catalog_id not Created at location test/path, assume parent is missing",
        ),
        (
            "POST",
            409,
            {"message": "Conflict"},
            "CONFLICT: Catalog: catalog_id already exists at location test/path",
        ),
        (
            "PUT",
            200,
            {"message": "Entry Updated Successfully"},
            "Updated Catalog: catalog_id at location test/path",
        ),
        (
            "PUT",
            404,
            {"message": "Not Found"},
            "NOT_FOUND: Catalog: catalog_id not Updated as entry at location test/path doesn't exist",
        ),
        (
            "PUT",
            500,
            {"message": "Some Other Error"},
            "Catalog: catalog_id not Updated at location test/path",
        ),
    ],
)
def test_log_response(req_method, status_code, response_json, expected_exception, caplog):
    """
    Test the log_response function.
    """

    # Set logging level
    caplog.set_level(logging.INFO)

    # Set variables
    response = mock.Mock()
    response.status_code = status_code
    response.request.method = req_method
    response.json.return_value = response_json
    data_id = "catalog_id"
    catalog_path = "test/path"
    api_url = "https://test-url/api"
    data_type = "Catalog"

    log_response(response, data_id, catalog_path, api_url, data_type)

    # Assertions
    assert expected_exception in caplog.text


@pytest.mark.parametrize(
    "req_method, status_code, response_json, expected_exception",
    [
        ("POST", 204, {"message": "Entry Deleted Successfully"}, "Deleted entry at test/path"),
        (
            "POST",
            404,
            {"message": "Not Found"},
            "NOT_FOUND: Failed to Delete entry at test/path as it doesn't exist",
        ),
        ("POST", 409, {"message": "Conflict"}, "Entry at test/path not Deleted"),
    ],
)
def test_log_response_delete(req_method, status_code, response_json, expected_exception, caplog):
    """
    Test the log_response_delete function.
    """

    # Set logging level
    caplog.set_level(logging.INFO)

    # Set variables
    response = mock.Mock()
    response.status_code = status_code
    response.request.method = req_method
    response.json.return_value = response_json
    catalog_path = "test/path"
    api_url = "https://test-url/api"

    log_response_delete(response, catalog_path, api_url)

    # Assertions
    assert expected_exception in caplog.text
