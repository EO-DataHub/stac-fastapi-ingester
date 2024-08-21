import json
import os
from io import BytesIO
from unittest import mock
from unittest.mock import patch

import botocore
import pytest
import requests
from botocore.exceptions import ClientError
from click.testing import CliRunner

from stac_fastapi_ingester.__main__ import (
    cli,
    create_catalog,
    create_collection,
    create_item,
    delete_catalog,
    delete_collection,
    delete_item,
    interpret_message,
    load_data_from_s3,
    update_catalog,
    update_collection,
    update_item,
)

###################
## Test Catalogs ##
###################


@pytest.mark.parametrize(
    "http_method, status_code, api_url, data, catalog_path, "
    "call_count, expected_url, expected_headers, expected_log",
    [
        (  ## create_catalog_success
            "POST",
            200,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: OK",
        ),
        (  # create_catalog_conflict
            "POST",
            409,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: CONFLICT",
        ),
        (  # create_catalog_not_found
            "POST",
            404,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: NOT_FOUND",
        ),
        (  # create_catalog_error
            "POST",
            400,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: 400",
        ),
        (  # update_catalog_success
            "PUT",
            200,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/test_catalog_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: OK",
        ),
        (  # update_catalog_conflict
            "PUT",
            409,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/test_catalog_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: CONFLICT",
        ),
        (  # update_catalog_not_found
            "PUT",
            404,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/test_catalog_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: NOT_FOUND",
        ),
        (  # update_catalog_error
            "PUT",
            400,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/test_catalog_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: 400",
        ),
        (  # delete_catalog_success
            "DELETE",
            200,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/test_catalog_id",
            {"accept": "application/json"},
            "Status Code: OK",
        ),
        (  # delete_catalog_conflict
            "DELETE",
            409,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/test_catalog_id",
            {"accept": "application/json"},
            "Status Code: CONFLICT",
        ),
        (  # delete_catalog_not_found
            "DELETE",
            404,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/test_catalog_id",
            {"accept": "application/json"},
            "Status Code: NOT_FOUND",
        ),
        (  # delete_catalog_error
            "DELETE",
            400,
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/test_catalog_id",
            {"accept": "application/json"},
            "Status Code: 400",
        ),
    ],
)
def test_handle_catalogs(
    caplog,
    http_method,
    status_code,
    api_url,
    data,
    catalog_path,
    call_count,
    expected_url,
    expected_headers,
    expected_log,
    requests_mock,
):

    # Mock the requests calls
    requests_mock.post(expected_url, status_code=status_code)
    requests_mock.put(expected_url, status_code=status_code)
    requests_mock.delete(expected_url, status_code=status_code)

    if http_method == "POST":
        create_catalog(api_url, data, catalog_path)
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "PUT":
        update_catalog(api_url, data, catalog_path, "test_catalog_id")
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "DELETE":
        delete_catalog(api_url, catalog_path, "test_catalog_id")
        expected_kwargs = {"headers": expected_headers}

    # Assert that the request was made correct number of times
    assert requests_mock.called
    assert requests_mock.call_count == call_count

    # Check requests was made with expected arguments
    request = requests_mock.request_history[0]
    assert request.method == http_method

    for arg in expected_kwargs:
        if arg == "headers":
            for header in expected_kwargs[arg]:
                # Only need to check headers added by the function
                assert request.headers[header] == expected_headers[header]
        elif arg == "json":
            assert request.json() == expected_kwargs[arg]

    # Check output log is correct
    assert expected_log in caplog.text


@pytest.mark.parametrize(
    "http_method, api_url, data, catalog_id, catalog_path, "
    "call_count, expected_url, expected_headers, expected_log",
    [
        (  # create
            "POST",
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "test_catalog_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Catalog: test_catalog_id not created",
        ),
        (  # update
            "PUT",
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "test_catalog_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/test_catalog_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Catalog: test_catalog_id at example/path/to/catalog not updated",
        ),
        (  # delete
            "DELETE",
            "https://test-url/api",
            {"id": "test_catalog_id"},
            "test_catalog_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/test_catalog_id",
            {"accept": "application/json"},
            "Catalog: test_catalog_id not deleted",
        ),
    ],
)
def test_catalog_connection_error(
    caplog,
    http_method,
    api_url,
    data,
    catalog_id,
    catalog_path,
    call_count,
    expected_url,
    expected_headers,
    expected_log,
    requests_mock,
):

    # Mock the requests calls
    requests_mock.post(expected_url, exc=requests.ConnectionError)
    requests_mock.put(expected_url, exc=requests.ConnectionError)
    requests_mock.delete(expected_url, exc=requests.ConnectionError)

    if http_method == "POST":
        with pytest.raises(requests.ConnectionError):
            create_catalog(api_url, data, catalog_path)
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "PUT":
        with pytest.raises(requests.ConnectionError):
            update_catalog(api_url, data, catalog_path, catalog_id)
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "DELETE":
        with pytest.raises(requests.ConnectionError):
            delete_catalog(api_url, catalog_path, catalog_id)
        expected_kwargs = {"headers": expected_headers}

    # Assert that the request was made correct number of times
    assert requests_mock.called
    assert requests_mock.call_count == call_count

    # Check requests was made with expected arguments
    request = requests_mock.request_history[0]
    assert request.method == http_method

    for arg in expected_kwargs:
        if arg == "headers":
            for header in expected_kwargs[arg]:
                # Only need to check headers added by the function
                assert request.headers[header] == expected_headers[header]
        elif arg == "json":
            assert request.json() == expected_kwargs[arg]

    # Check output log is correct
    assert expected_log in caplog.text


######################
## Test Collections ##
######################


@pytest.mark.parametrize(
    "http_method, status_code, api_url, data, collection_id, catalog_path, "
    "call_count, expected_url, expected_headers, expected_log",
    [
        (  # create_collection_success
            "POST",
            200,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: OK",
        ),
        (  # create_collection_conflict
            "POST",
            409,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: CONFLICT",
        ),
        (  # create_collection_not_found
            "POST",
            404,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Catalog: example/path/to/catalog not yet created",
        ),
        (  # create_collection_error
            "POST",
            400,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: 400",
        ),
        (  # update_collection_success
            "PUT",
            200,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: OK",
        ),
        (  # update_collection_conflict
            "PUT",
            409,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: CONFLICT",
        ),
        (  # update_collection_not_found
            "PUT",
            404,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: NOT_FOUND",
        ),
        (  # update_collection_error
            "PUT",
            400,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Status Code: 400",
        ),
        (  # delete_collection_success
            "DELETE",
            200,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id",
            {"accept": "application/json"},
            "Status Code: OK",
        ),
        (  # delete_collection_conflict
            "DELETE",
            409,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id",
            {"accept": "application/json"},
            "Status Code: CONFLICT",
        ),
        (  # delete_collection_not_found
            "DELETE",
            404,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id",
            {"accept": "application/json"},
            "Status Code: NOT_FOUND",
        ),
        (  # delete_collection_error
            "DELETE",
            400,
            "https://test-url/api",
            {"id": "test_collection_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id",
            {"accept": "application/json"},
            "Status Code: 400",
        ),
    ],
)
def test_handle_collections(
    caplog,
    http_method,
    status_code,
    api_url,
    data,
    collection_id,
    catalog_path,
    call_count,
    expected_url,
    expected_headers,
    expected_log,
    requests_mock,
):

    # Mock the requests calls
    requests_mock.post(expected_url, status_code=status_code)
    requests_mock.put(expected_url, status_code=status_code)
    requests_mock.delete(expected_url, status_code=status_code)

    if http_method == "POST":
        create_collection(api_url, collection_id, data, catalog_path)
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "PUT":
        update_collection(api_url, collection_id, data, catalog_path)
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "DELETE":
        delete_collection(api_url, collection_id, catalog_path)
        expected_kwargs = {"headers": expected_headers}

    # Assert that the request was made correct number of times
    assert requests_mock.called
    assert requests_mock.call_count == call_count

    # Check requests was made with expected arguments
    request = requests_mock.request_history[0]
    assert request.method == http_method

    for arg in expected_kwargs:
        if arg == "headers":
            for header in expected_kwargs[arg]:
                # Only need to check headers added by the function
                assert request.headers[header] == expected_headers[header]
        elif arg == "json":
            assert request.json() == expected_kwargs[arg]

    # Check output log is correct
    assert expected_log in caplog.text


@pytest.mark.parametrize(
    "http_method, api_url, data, collection_id, catalog_path, "
    "call_count, expected_url, expected_headers, expected_log",
    [
        (  # create
            "POST",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Collection: test_collection_id not created",
        ),
        (  # update
            "PUT",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Collection: test_collection_id in Catalog: example/path/to/catalog not updated",
        ),
        (  # delete
            "DELETE",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id",
            {"accept": "application/json"},
            "Collection: test_collection_id not deleted",
        ),
    ],
)
def test_collection_connection_error(
    caplog,
    http_method,
    api_url,
    data,
    collection_id,
    catalog_path,
    call_count,
    expected_url,
    expected_headers,
    expected_log,
    requests_mock,
):

    # Mock the requests calls
    requests_mock.post(expected_url, exc=requests.ConnectionError)
    requests_mock.put(expected_url, exc=requests.ConnectionError)
    requests_mock.delete(expected_url, exc=requests.ConnectionError)

    if http_method == "POST":
        with pytest.raises(requests.ConnectionError):
            create_collection(api_url, collection_id, data, catalog_path)
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "PUT":
        with pytest.raises(requests.ConnectionError):
            update_collection(api_url, collection_id, data, catalog_path)
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "DELETE":
        with pytest.raises(requests.ConnectionError):
            delete_collection(api_url, collection_id, catalog_path)
        expected_kwargs = {"headers": expected_headers}

    # Assert that the request was made correct number of times
    assert requests_mock.called
    assert requests_mock.call_count == call_count

    # Check requests was made with expected arguments
    request = requests_mock.request_history[0]
    assert request.method == http_method

    for arg in expected_kwargs:
        if arg == "headers":
            for header in expected_kwargs[arg]:
                # Only need to check headers added by the function
                assert request.headers[header] == expected_headers[header]
        elif arg == "json":
            assert request.json() == expected_kwargs[arg]

    # Check output log is correct
    assert expected_log in caplog.text


######################
## Test Items ##
######################


@pytest.mark.parametrize(
    "http_method, status_code, error_description, api_url, data, collection_id, "
    "item_id, catalog_path, call_count, expected_url, expected_headers, expected_log",
    [
        (  # create_item_success
            "POST",
            200,
            "",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items",
            {"accept": "application/json", "Content-Type": "application/json"},
            ["Status Code: OK"],
        ),
        (  # create_item_conflict
            "POST",
            409,
            "",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items",
            {"accept": "application/json", "Content-Type": "application/json"},
            ["Status Code: CONFLICT"],
        ),
        (  # create_item_not_found
            "POST",
            404,
            "",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items",
            {"accept": "application/json", "Content-Type": "application/json"},
            ["Collection: test_collection_id or Catalog: example/path/to/catalog not yet created"],
        ),
        (  # create_item_error
            "POST",
            400,
            "",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items",
            {"accept": "application/json", "Content-Type": "application/json"},
            ["Status Code: 400"],
        ),
        (  # update_item_success
            "PUT",
            200,
            "",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items/test_item_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            ["Status Code: OK"],
        ),
        (  # update_item_conflict
            "PUT",
            409,
            "",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items/test_item_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            ["Status Code: CONFLICT"],
        ),
        (  # update_item_not_found_item
            "PUT",
            404,
            "Item",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items/test_item_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            ["Status Code: NOT_FOUND", "item doesn't exist"],
        ),
        (  # update_item_not_found_collection
            "PUT",
            404,
            "Collection",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items/test_item_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            ["Status Code: NOT_FOUND", "collection doesn't exist"],
        ),
        (  # update_item_not_found_catalog
            "PUT",
            404,
            "Catalog",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items/test_item_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            ["Status Code: NOT_FOUND", "catalog doesn't exist"],
        ),
        (  # update_item_error
            "PUT",
            400,
            "",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items/test_item_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            ["Status Code: 400"],
        ),
        (  # delete_item_success
            "DELETE",
            200,
            "",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items/test_item_id",
            {"accept": "application/json"},
            ["Status Code: OK"],
        ),
        (  # delete_item_conflict
            "DELETE",
            409,
            "",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items/test_item_id",
            {"accept": "application/json"},
            ["Status Code: CONFLICT"],
        ),
        (  # delete_item_not_found
            "DELETE",
            404,
            "",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items/test_item_id",
            {"accept": "application/json"},
            ["Status Code: NOT_FOUND"],
        ),
        (  # delete_item_error
            "DELETE",
            400,
            "",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items/test_item_id",
            {"accept": "application/json"},
            ["Status Code: 400"],
        ),
    ],
)
def test_handle_items(
    caplog,
    http_method,
    status_code,
    error_description,
    api_url,
    data,
    collection_id,
    item_id,
    catalog_path,
    call_count,
    expected_url,
    expected_headers,
    expected_log,
    requests_mock,
):

    # Create mocks
    mock_content = f'{{"description": "{error_description}"}}'.encode("utf-8")

    # Mock the requests calls
    requests_mock.post(expected_url, status_code=status_code)
    requests_mock.put(expected_url, status_code=status_code, content=mock_content)
    requests_mock.delete(expected_url, status_code=status_code)

    if http_method == "POST":
        create_item(api_url, collection_id, item_id, data, catalog_path)
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "PUT":
        update_item(api_url, collection_id, item_id, data, catalog_path)
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "DELETE":
        delete_item(api_url, collection_id, item_id, catalog_path)
        expected_kwargs = {"headers": expected_headers}

    # Assert that the request was made correct number of times
    assert requests_mock.called
    assert requests_mock.call_count == call_count

    # Check requests was made with expected arguments
    request = requests_mock.request_history[0]
    assert request.method == http_method

    for arg in expected_kwargs:
        if arg == "headers":
            for header in expected_kwargs[arg]:
                # Only need to check headers added by the function
                assert request.headers[header] == expected_headers[header]
        elif arg == "json":
            assert request.json() == expected_kwargs[arg]

    # Check output log is correct
    for log in expected_log:
        assert log in caplog.text


@pytest.mark.parametrize(
    "http_method, api_url, data, collection_id, item_id, catalog_path, "
    "call_count, expected_url, expected_headers, expected_log",
    [
        (  # create
            "POST",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Item: test_item_id in Collection: test_collection_id in Catalog: "
            "example/path/to/catalog not created",
        ),
        (  # update
            "PUT",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/test_collection_id/items/test_item_id",
            {"accept": "application/json", "Content-Type": "application/json"},
            "Item: test_item_id in Collection: test_collection_id in "
            "Catalog: example/path/to/catalog not updated",
        ),
        (  # delete
            "DELETE",
            "https://test-url/api",
            {"id": "test_item_id"},
            "test_collection_id",
            "test_item_id",
            "example/path/to/catalog",
            1,
            "https://test-url/api/catalogs/example/path/to/catalog/collections/"
            "test_collection_id/items/test_item_id",
            {"accept": "application/json"},
            "Item: test_item_id in Collection: test_collection_id in "
            "Catalog: example/path/to/catalog not deleted",
        ),
    ],
)
def test_item_connection_error(
    caplog,
    http_method,
    api_url,
    data,
    collection_id,
    item_id,
    catalog_path,
    call_count,
    expected_url,
    expected_headers,
    expected_log,
    requests_mock,
):

    # Mock the requests calls
    requests_mock.post(expected_url, exc=requests.ConnectionError)
    requests_mock.put(expected_url, exc=requests.ConnectionError)
    requests_mock.delete(expected_url, exc=requests.ConnectionError)

    if http_method == "POST":
        with pytest.raises(requests.ConnectionError):
            create_item(api_url, collection_id, item_id, data, catalog_path)
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "PUT":
        with pytest.raises(requests.ConnectionError):
            update_item(api_url, collection_id, item_id, data, catalog_path)
        expected_kwargs = {"headers": expected_headers, "json": data}
    elif http_method == "DELETE":
        with pytest.raises(requests.ConnectionError):
            delete_item(api_url, collection_id, item_id, catalog_path)
        expected_kwargs = {"headers": expected_headers}

    # Assert that the request was made correct number of times
    assert requests_mock.called
    assert requests_mock.call_count == call_count

    # Check requests was made with expected arguments
    request = requests_mock.request_history[0]
    assert request.method == http_method

    for arg in expected_kwargs:
        if arg == "headers":
            for header in expected_kwargs[arg]:
                # Only need to check headers added by the function
                assert request.headers[header] == expected_headers[header]
        elif arg == "json":
            assert request.json() == expected_kwargs[arg]

    # Check output log is correct
    assert expected_log in caplog.text


############################
## Test Interpret Message ##
############################


@pytest.mark.parametrize(
    "http_method, api_url, test_id",
    [
        (  # create
            "POST",
            "https://test-url/api",
            "test_catalog_id",
        ),
        (  # update
            "PUT",
            "https://test-url/api",
            "test_catalog_id",
        ),
        (  # delete
            "DELETE",
            "https://test-url/api",
            "test_catalog_id",
        ),
    ],
)
@patch("stac_fastapi_ingester.__main__.delete_catalog")
@patch("stac_fastapi_ingester.__main__.update_catalog")
@patch("stac_fastapi_ingester.__main__.create_catalog")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_catalog(
    mock_load_data_from_s3,
    mock_create_catalog,
    mock_update_catalog,
    mock_delete_catalog,
    http_method,
    api_url,
    test_id,
):

    # Configure test variables
    test_id = "test_catalog_id"
    test_key = f"transformed/catalog_key_1/{test_id}"
    test_catalog_path = "catalog_key_1"
    test_data = {"id": test_id, "type": "Catalog"}

    # Setup mocks based on the http_method parameter
    if http_method == "POST":
        mock_function = mock_create_catalog
        added_keys = f'["{test_key}"]'
        update_keys = "[]"
        delete_keys = "[]"
        expected_args = (api_url, test_data, test_catalog_path)
    elif http_method == "PUT":
        mock_function = mock_update_catalog
        added_keys = "[]"
        update_keys = f'["{test_key}"]'
        delete_keys = "[]"
        expected_args = (api_url, test_data, test_catalog_path, test_id)
    elif http_method == "DELETE":
        mock_function = mock_delete_catalog
        added_keys = "[]"
        update_keys = "[]"
        delete_keys = f'["{test_key}"]'
        expected_args = (api_url, test_catalog_path, test_id)
    else:
        raise ValueError("Unsupported HTTP method")

    # Construct test Pulsar input message
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": {update_keys},
        "added_keys": {added_keys},
        "deleted_keys": {delete_keys},
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_function.return_value = None

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_function.call_count == 1
    mock_function.assert_called_once_with(*expected_args)


@pytest.mark.parametrize(
    "http_method, success",
    [
        ("POST", True),  # create success
        ("POST", False),  # create fail
        ("PUT", True),  # update success
        ("PUT", False),  # update fail
        ("DELETE", True),  # delete success
    ],
)
@patch("stac_fastapi_ingester.__main__.delete_collection")
@patch("stac_fastapi_ingester.__main__.update_collection")
@patch("stac_fastapi_ingester.__main__.create_collection")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_collection(
    mock_load_data_from_s3,
    mock_create_collection,
    mock_update_collection,
    mock_delete_collection,
    http_method,
    success,
):

    # Configure test variables
    test_id = "test_collection_id"
    test_key = f"transformed/catalog_key_1/{test_id}"
    test_catalog_path = "catalog_key_1"
    test_data = {"id": test_id, "type": "Collection"}
    api_url = "https://test-url/api"

    # Setup mocks based on the http_method parameter
    if http_method == "POST":
        mock_function = mock_create_collection
        added_keys = f'["{test_key}"]'
        update_keys = "[]"
        delete_keys = "[]"
        expected_args = (api_url, test_id, test_data, test_catalog_path)
    elif http_method == "PUT":
        mock_function = mock_update_collection
        added_keys = "[]"
        update_keys = f'["{test_key}"]'
        delete_keys = "[]"
        expected_args = (api_url, test_id, test_data, test_catalog_path)
    elif http_method == "DELETE":
        mock_function = mock_delete_collection
        added_keys = "[]"
        update_keys = "[]"
        delete_keys = f'["{test_key}"]'
        expected_args = (api_url, test_id, test_catalog_path)
    else:
        raise ValueError("Unsupported HTTP method")

    # Construct test Pulsar input message
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": {update_keys},
        "added_keys": {added_keys},
        "deleted_keys": {delete_keys},
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_function.return_value = success  # either success (True) or fail (False)

    # Call function
    interpret_message(test_msg, api_url)

    if success:
        # Check function called as expected
        assert mock_function.call_count == 1
        mock_function.assert_called_once_with(*expected_args)
    else:
        # Check function called as expected
        assert mock_function.call_count == 3

        # Ensure all three calls are identical
        calls = mock_function.call_args_list
        for i in range(3):
            assert calls[i].args == expected_args


@pytest.mark.parametrize(
    "http_method, success",
    [
        ("POST", True),  # create success
        ("POST", False),  # create fail
        ("PUT", True),  # update success
        ("PUT", False),  # update fail
        ("DELETE", True),  # delete success
    ],
)
@patch("stac_fastapi_ingester.__main__.delete_item")
@patch("stac_fastapi_ingester.__main__.update_item")
@patch("stac_fastapi_ingester.__main__.create_item")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_item(
    mock_load_data_from_s3,
    mock_create_item,
    mock_update_item,
    mock_delete_item,
    http_method,
    success,
):

    # Configure test variables
    test_item_id = "item_key_1"
    test_collection_id = "collection_key_1"
    test_key = f"transformed/catalog_key_1/{test_collection_id}/{test_item_id}"
    test_catalog_path = "catalog_key_1"
    test_data = {"id": test_item_id, "type": "Collection"}
    api_url = "https://test-url/api"
    test_data = {"id": test_item_id, "type": "Feature", "collection": test_collection_id}

    # Setup mocks based on the http_method parameter
    if http_method == "POST":
        mock_function = mock_create_item
        added_keys = f'["{test_key}"]'
        update_keys = "[]"
        delete_keys = "[]"
        expected_args = (api_url, test_collection_id, test_item_id, test_data, test_catalog_path)
    elif http_method == "PUT":
        mock_function = mock_update_item
        added_keys = "[]"
        update_keys = f'["{test_key}"]'
        delete_keys = "[]"
        expected_args = (api_url, test_collection_id, test_item_id, test_data, test_catalog_path)
    elif http_method == "DELETE":
        mock_function = mock_delete_item
        added_keys = "[]"
        update_keys = "[]"
        delete_keys = f'["{test_key}"]'
        expected_args = (api_url, test_collection_id, test_item_id, test_catalog_path)
    else:
        raise ValueError("Unsupported HTTP method")

    # Construct test Pulsar input message
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": {update_keys},
        "added_keys": {added_keys},
        "deleted_keys": {delete_keys},
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_function.return_value = success  # either success (True) or fail (False)

    # Call function
    interpret_message(test_msg, api_url)

    if success:
        # Check function called as expected
        assert mock_function.call_count == 1
        mock_function.assert_called_once_with(*expected_args)
    else:
        # Check function called as expected
        assert mock_function.call_count == 3

        # Ensure all three calls are identical
        calls = mock_function.call_args_list
        for i in range(3):
            assert calls[i].args == expected_args


##############
## Test CLI ##
##############


@patch.dict(os.environ, {"PULSAR_URL": "pulsar://test-url", "FASTAPI_URL": "https://test-url/api"})
@patch("stac_fastapi_ingester.__main__.interpret_message")
@patch("pulsar.Client")
def test_cli_with_topic_and_pulsar_url(mock_pulsar_client, mock_interpret_message, caplog):

    # Configure mocks
    mock_pulsar_client_instance = mock.Mock()
    mock_pulsar_client_consumer = mock.Mock()
    mock_received_message = mock.Mock()
    mock_received_message.data.return_value = b"this is a test message"
    mock_pulsar_client_consumer.acknowledge.return_value = None
    # This set of returns runs the loop once and then throws an error, to avoid endless looping
    mock_pulsar_client_consumer.receive.side_effect = [mock_received_message, StopIteration]
    mock_pulsar_client_instance.subscribe.return_value = mock_pulsar_client_consumer
    mock_pulsar_client.return_value = mock_pulsar_client_instance
    mock_interpret_message.return_value = None

    # Set up the CliRunner
    runner = CliRunner()

    # Invoke the CLI with a test topic
    result = runner.invoke(cli, ["test-topic", "subscribe", "--prefix", "test_name"])

    # Assertions
    # Check the CLI ran successfully
    assert result.exit_code == 0

    # Check the Pulsar calls and response
    mock_pulsar_client.assert_called_once_with("pulsar://test-url")
    assert "Connecting to broker 'pulsar://test-url' with topic 'test-topic'" in caplog.text

    # Check message is received correctly
    assert "this is a test message" in caplog.text

    # Check the subsequent calls are correct
    assert (
        mock_pulsar_client_consumer.receive.call_count == 2
    )  # note, this errors on second run to terminate loop
    mock_interpret_message.assert_called_once_with("this is a test message", "https://test-url/api")
    mock_pulsar_client_consumer.acknowledge.assert_called_once_with(mock_received_message)


############################
## Test Load Data from S3 ##
############################


def test_load_data_from_s3_success(caplog):

    # Set test variables
    bucket_name = "test_bucket"
    file_key = "test_key"

    # Create mocks
    mock_botocore_client = mock.Mock()
    byte_string = b"""{"id": "test_id"}"""
    mock_botocore_client.get_object.return_value = {"Body": BytesIO(byte_string)}

    # Call the function under test
    result = load_data_from_s3(mock_botocore_client, bucket_name, file_key)

    assert result == {"id": "test_id"}


def test_load_data_from_s3_param_error(caplog):

    # Set test variables
    bucket_name = "test_bucket"
    file_key = "test_key"

    # Create mocks
    mock_botocore_client = mock.Mock()
    mock_botocore_client.get_object.side_effect = botocore.exceptions.ParamValidationError(
        report="Invalid parameters"
    )

    # Call the function under test
    result = load_data_from_s3(mock_botocore_client, bucket_name, file_key)

    # Assert that warning is raised correctly
    assert not result
    assert "Provided bucket name or file key is not supported." in caplog.text


def test_load_data_from_s3_json_decode_error(caplog):

    # Set test variables
    bucket_name = "test_bucket"
    file_key = "test_key"

    # Create mocks
    mock_botocore_client = mock.Mock()
    mock_botocore_client.get_object.side_effect = json.decoder.JSONDecodeError(
        msg="Invalid JSON", doc="", pos=0
    )

    # Call the function under test
    result = load_data_from_s3(mock_botocore_client, bucket_name, file_key)

    # Assert that warning is raised correctly
    assert not result
    assert f"File {file_key} is not a JSON file. Ignoring." in caplog.text


def test_load_data_from_s3_unicode_decode_error(caplog):

    # Set test variables
    bucket_name = "test_bucket"
    file_key = "test_key"

    # Create mocks
    mock_botocore_client = mock.Mock()
    mock_botocore_client.get_object.side_effect = UnicodeDecodeError(
        "utf-8", b"", 0, 1, "invalid start byte"
    )

    # Call the function under test
    result = load_data_from_s3(mock_botocore_client, bucket_name, file_key)

    # Assert that warning is raised correctly
    assert not result
    assert f"File {file_key} is not a JSON file. Ignoring." in caplog.text


def test_load_data_from_s3_other_error(caplog):

    # Set test variables
    bucket_name = "test_bucket"
    file_key = "test_key"

    # Create mocks
    mock_botocore_client = mock.Mock()
    mock_botocore_client.get_object.side_effect = RuntimeError("An error occurred")

    # Call the function under test
    with pytest.raises(RuntimeError):
        load_data_from_s3(mock_botocore_client, bucket_name, file_key)

    # Assert that warning is raised correctly
    assert f"Failed to load S3 object with key: {file_key}" in caplog.text


def test_load_data_from_s3_botocore_key_error(caplog):

    # Set test variables
    bucket_name = "test_bucket"
    file_key = "test_key"

    # Create mocks
    mock_botocore_client = mock.Mock()
    error_response = {
        "Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}
    }
    mock_botocore_client.get_object.side_effect = ClientError(error_response, "GetObject")

    # Call the function under test
    result = load_data_from_s3(mock_botocore_client, bucket_name, file_key)

    # Assert that warning is raised correctly
    assert not result
    assert f"File {file_key} does not exist in S3. Ignoring." in caplog.text


def test_load_data_from_s3_botocore_error(caplog):

    # Set test variables
    bucket_name = "test_bucket"
    file_key = "test_key"

    # Create mocks
    mock_botocore_client = mock.Mock()
    error_response = {"Error": {"Code": "Other", "Message": "The specified key does not exist."}}
    mock_botocore_client.get_object.side_effect = ClientError(error_response, "GetObject")

    # Call the function under test
    with pytest.raises(ClientError):
        load_data_from_s3(mock_botocore_client, bucket_name, file_key)

    # Assert that warning is raised correctly
    assert f"Failed to load S3 object with key: {file_key}" in caplog.text
