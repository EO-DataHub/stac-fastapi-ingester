import os
from unittest import mock
from unittest.mock import patch

import pytest
import requests
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
    update_catalog,
    update_collection,
    update_item,
)

#########################
## Test Create Catalog ##
#########################


@patch("requests.post")
def test_create_catalog_success(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_post.return_value = mock_object

    create_catalog(api_url, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: OK" in caplog.text


@patch("requests.post")
def test_create_catalog_conflict(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 409
    mock_requests_post.return_value = mock_object

    create_catalog(api_url, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: CONFLICT" in caplog.text


@patch("requests.post")
def test_create_catalog_not_found(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 404
    mock_requests_post.return_value = mock_object

    create_catalog(api_url, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: NOT_FOUND" in caplog.text


@patch("requests.post")
def test_create_catalog_error(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 400
    mock_requests_post.return_value = mock_object

    create_catalog(api_url, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status Code: 400" in caplog.text


@patch("requests.post")
def test_create_catalog_connection_error(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    data = {"id": test_id}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_post.side_effect = requests.ConnectionError

    # Execute and assert that requests.ConnectionError is raised
    with pytest.raises(requests.ConnectionError):
        create_catalog(api_url, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert f"Catalog: {test_id} not created" in caplog.text


#########################
## Test Update Catalog ##
#########################


@patch("requests.put")
def test_update_catalog_success(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    data = {"id": test_id}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/{test_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_put.return_value = mock_object

    update_catalog(api_url, data, catalog_path, test_id)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: OK" in caplog.text


@patch("requests.put")
def test_update_catalog_conflict(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    data = {"id": test_id}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/{test_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 409
    mock_requests_put.return_value = mock_object

    update_catalog(api_url, data, catalog_path, test_id)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: CONFLICT" in caplog.text


@patch("requests.put")
def test_update_catalog_not_found(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    data = {"id": test_id}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/{test_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 404
    mock_requests_put.return_value = mock_object

    update_catalog(api_url, data, catalog_path, test_id)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: NOT_FOUND" in caplog.text


@patch("requests.put")
def test_update_catalog_error(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    data = {"id": test_id}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/{test_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 400
    mock_requests_put.return_value = mock_object

    update_catalog(api_url, data, catalog_path, test_id)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status Code: 400" in caplog.text


@patch("requests.put")
def test_update_catalog_connection_error(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    data = {"id": test_id}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/{test_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_put.side_effect = requests.ConnectionError

    # Execute and assert that requests.ConnectionError is raised
    with pytest.raises(requests.ConnectionError):
        update_catalog(api_url, data, catalog_path, test_id)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert f"Catalog: {test_id} at {catalog_path} not updated" in caplog.text


#########################
## Test Delete Catalog ##
#########################


@patch("requests.delete")
def test_delete_catalog_success(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_delete.return_value = mock_object

    delete_catalog(api_url, catalog_path, test_id)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status code: OK" in caplog.text


@patch("requests.delete")
def test_delete_catalog_conflict(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 409
    mock_requests_delete.return_value = mock_object

    delete_catalog(api_url, catalog_path, test_id)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status code: CONFLICT" in caplog.text


@patch("requests.delete")
def test_delete_catalog_not_found(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 404
    mock_requests_delete.return_value = mock_object

    delete_catalog(api_url, catalog_path, test_id)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status code: NOT_FOUND" in caplog.text


@patch("requests.delete")
def test_delete_catalog_error(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 400
    mock_requests_delete.return_value = mock_object

    delete_catalog(api_url, catalog_path, test_id)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status Code: 400" in caplog.text


@patch("requests.delete")
def test_delete_catalog_connection_error(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_delete.side_effect = requests.ConnectionError

    # Execute and assert that requests.ConnectionError is raised
    with pytest.raises(requests.ConnectionError):
        delete_catalog(api_url, catalog_path, test_id)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert f"Catalog: {test_id} not deleted" in caplog.text


############################
## Test Create Collection ##
############################


@patch("requests.post")
def test_create_collection_success(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_post.return_value = mock_object

    create_collection(api_url, collection_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: OK" in caplog.text


@patch("requests.post")
def test_create_collection_conflict(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 409
    mock_requests_post.return_value = mock_object

    create_collection(api_url, collection_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: CONFLICT" in caplog.text


@patch("requests.post")
def test_create_collection_not_found(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 404
    mock_requests_post.return_value = mock_object

    create_collection(api_url, collection_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert f"Catalog: {catalog_path} not yet created" in caplog.text


@patch("requests.post")
def test_create_collection_error(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 400
    mock_requests_post.return_value = mock_object

    create_collection(api_url, collection_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status Code: 400" in caplog.text


@patch("requests.post")
def test_create_collection_connection_error(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_post.side_effect = requests.ConnectionError

    # Execute and assert that requests.ConnectionError is raised
    with pytest.raises(requests.ConnectionError):
        create_collection(api_url, collection_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert f"Collection: {collection_id} not created" in caplog.text


############################
## Test Update Collection ##
############################


@patch("requests.put")
def test_update_collection_success(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_put.return_value = mock_object

    update_collection(api_url, collection_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: OK" in caplog.text


@patch("requests.put")
def test_update_collection_conflict(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 409
    mock_requests_put.return_value = mock_object

    update_collection(api_url, collection_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: CONFLICT" in caplog.text


@patch("requests.put")
def test_update_collection_not_found(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 404
    mock_requests_put.return_value = mock_object

    update_collection(api_url, collection_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: NOT_FOUND" in caplog.text


@patch("requests.put")
def test_update_collection_error(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 400
    mock_requests_put.return_value = mock_object

    update_collection(api_url, collection_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status Code: 400" in caplog.text


@patch("requests.put")
def test_update_collection_connection_error(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_put.side_effect = requests.ConnectionError

    # Execute and assert that requests.ConnectionError is raised
    with pytest.raises(requests.ConnectionError):
        update_collection(api_url, collection_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert f"Collection: {collection_id} in Catalog: {catalog_path} not updated" in caplog.text


############################
## Test Delete Collection ##
############################


@patch("requests.delete")
def test_delete_collection_success(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_delete.return_value = mock_object

    delete_collection(api_url, test_id, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status code: OK" in caplog.text


@patch("requests.delete")
def test_delete_collection_conflict(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 409
    mock_requests_delete.return_value = mock_object

    delete_collection(api_url, test_id, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status code: CONFLICT" in caplog.text


@patch("requests.delete")
def test_delete_collection_not_found(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 404
    mock_requests_delete.return_value = mock_object

    delete_collection(api_url, test_id, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status code: NOT_FOUND" in caplog.text


@patch("requests.delete")
def test_delete_collection_error(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 400
    mock_requests_delete.return_value = mock_object

    delete_collection(api_url, test_id, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status Code: 400" in caplog.text


@patch("requests.delete")
def test_delete_collection_connection_error(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_delete.side_effect = requests.ConnectionError

    # Execute and assert that requests.ConnectionError is raised
    with pytest.raises(requests.ConnectionError):
        delete_collection(api_url, test_id, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert f"Collection: {test_id} not deleted" in caplog.text


######################
## Test Create Item ##
######################


@patch("requests.post")
def test_create_item_success(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_post.return_value = mock_object

    create_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: OK" in caplog.text


@patch("requests.post")
def test_create_item_conflict(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 409
    mock_requests_post.return_value = mock_object

    create_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: CONFLICT" in caplog.text


@patch("requests.post")
def test_create_item_not_found(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 404
    mock_requests_post.return_value = mock_object

    create_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert f"Collection: {collection_id} or Catalog: {catalog_path} not yet created" in caplog.text


@patch("requests.post")
def test_create_item_error(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 400
    mock_requests_post.return_value = mock_object

    create_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status Code: 400" in caplog.text


@patch("requests.post")
def test_create_item_connection_error(mock_requests_post, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_post.side_effect = requests.ConnectionError

    # Execute and assert that requests.ConnectionError is raised
    with pytest.raises(requests.ConnectionError):
        create_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_post.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_post.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert (
        f"Item: {item_id} in Collection: {collection_id} in Catalog: {catalog_path} not created not created"
        in caplog.text
    )


######################
## Test Update Item ##
######################


@patch("requests.put")
def test_update_item_success(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{item_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_put.return_value = mock_object

    update_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: OK" in caplog.text


@patch("requests.put")
def test_update_item_conflict(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{item_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 409
    mock_requests_put.return_value = mock_object

    update_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: CONFLICT" in caplog.text


@patch("requests.put")
def test_update_item_not_found_item(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": "test_id"}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{item_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 404
    mock_object.content.decode.return_value = '{"description": "Item"}'
    mock_requests_put.return_value = mock_object

    update_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: NOT_FOUND" in caplog.text
    assert "item doesn't exist." in caplog.text


@patch("requests.put")
def test_update_item_not_found_collection(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": item_id}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{item_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 404
    mock_object.content.decode.return_value = '{"description": "Collection"}'
    mock_requests_put.return_value = mock_object

    update_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: NOT_FOUND" in caplog.text
    assert "collection doesn't exist." in caplog.text


@patch("requests.put")
def test_update_item_not_found_catalog(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": item_id}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{item_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 404
    mock_object.content.decode.return_value = '{"description": "Catalog"}'
    mock_requests_put.return_value = mock_object
    mock_requests_put.return_value.json = {"message": "Not Found"}

    update_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status code: NOT_FOUND" in caplog.text
    assert "catalog doesn't exist." in caplog.text


@patch("requests.put")
def test_update_item_error(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": item_id}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{item_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 400
    mock_requests_put.return_value = mock_object

    update_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert "Status Code: 400" in caplog.text


@patch("requests.put")
def test_update_item_connection_error(mock_requests_put, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    item_id = "test_item"
    data = {"id": item_id}
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{item_id}"
    test_headers = {"accept": "application/json", "Content-Type": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_put.side_effect = requests.ConnectionError

    # Execute and assert that requests.ConnectionError is raised
    with pytest.raises(requests.ConnectionError):
        update_item(api_url, collection_id, item_id, data, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_put.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_put.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers, "json": data}

    # Check output log is correct
    assert (
        f"Item: {item_id} in Collection: {collection_id} in Catalog: {catalog_path} not updated"
        in caplog.text
    )


############################
## Test Delete Item ##
############################


@patch("requests.delete")
def test_delete_item_success(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_delete.return_value = mock_object

    delete_item(api_url, collection_id, test_id, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status code: OK" in caplog.text


@patch("requests.delete")
def test_delete_item_conflict(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 409
    mock_requests_delete.return_value = mock_object

    delete_item(api_url, collection_id, test_id, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status code: CONFLICT" in caplog.text


@patch("requests.delete")
def test_delete_item_not_found(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 404
    mock_requests_delete.return_value = mock_object

    delete_item(api_url, collection_id, test_id, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status code: NOT_FOUND" in caplog.text


@patch("requests.delete")
def test_delete_item_error(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 400
    mock_requests_delete.return_value = mock_object

    delete_item(api_url, collection_id, test_id, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert "Status Code: 400" in caplog.text


@patch("requests.delete")
def test_delete_item_connection_error(mock_requests_delete, caplog):

    # Set test variables
    api_url = "https://test-url/api"
    collection_id = "test_collection"
    test_id = "test_id"
    catalog_path = "example/path/to/catalog"
    test_url = f"{api_url}/catalogs/{catalog_path}/collections/{collection_id}/items/{test_id}"
    test_headers = {"accept": "application/json"}

    # Create mocks
    mock_object = mock.Mock()
    mock_object.status_code = 200
    mock_requests_delete.side_effect = requests.ConnectionError

    # Execute and assert that requests.ConnectionError is raised
    with pytest.raises(requests.ConnectionError):
        delete_item(api_url, collection_id, test_id, catalog_path)

    # Assert that the requests.post function was called once
    assert mock_requests_delete.call_count == 1

    # Check requests.post was called correctly
    calls = mock_requests_delete.call_args_list
    assert calls[0].args[0] == test_url
    assert calls[0].kwargs == {"headers": test_headers}

    # Check output log is correct
    assert (
        f"Item: {test_id} in Collection: {collection_id} in Catalog: {catalog_path} not deleted"
        in caplog.text
    )


############################
## Test Interpret Message ##
############################


@patch("stac_fastapi_ingester.__main__.create_catalog")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_create_catalog(mock_load_data_from_s3, mock_create_catalog):

    # Configure test variables
    test_id = "test_id"
    test_key = f"transformed/catalog_key_1/{test_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": [],
        "added_keys": ["{test_key}"],
        "deleted_keys": [],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_id, "type": "Catalog"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_create_catalog.return_value = None

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_create_catalog.call_count == 1
    mock_create_catalog.assert_called_once_with(api_url, test_data, test_catalog_path)


@patch("stac_fastapi_ingester.__main__.update_catalog")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_update_catalog(mock_load_data_from_s3, mock_update_catalog):

    # Configure test variables
    test_id = "test_id"
    test_key = f"transformed/catalog_key_1/{test_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": ["{test_key}"],
        "added_keys": [],
        "deleted_keys": [],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_id, "type": "Catalog"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_update_catalog.return_value = None

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_update_catalog.call_count == 1
    mock_update_catalog.assert_called_once_with(api_url, test_data, test_catalog_path, test_id)


@patch("stac_fastapi_ingester.__main__.delete_catalog")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_delete_catalog(mock_load_data_from_s3, mock_delete_catalog):

    # Configure test variables
    test_id = "test_id"
    test_key = f"transformed/catalog_key_1/{test_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": [],
        "added_keys": [],
        "deleted_keys": ["{test_key}"],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_id, "type": "Catalog"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_delete_catalog.return_value = None

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_delete_catalog.call_count == 1
    mock_delete_catalog.assert_called_once_with(api_url, test_catalog_path, test_id)


@patch("stac_fastapi_ingester.__main__.create_collection")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_create_collection_success(
    mock_load_data_from_s3, mock_create_collection
):

    # Configure test variables
    test_id = "test_id"
    test_key = f"transformed/catalog_key_1/{test_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": [],
        "added_keys": ["{test_key}"],
        "deleted_keys": [],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_id, "type": "Collection"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_create_collection.return_value = True  # created succesfully

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_create_collection.call_count == 1
    mock_create_collection.assert_called_once_with(api_url, test_id, test_data, test_catalog_path)


@patch("stac_fastapi_ingester.__main__.create_collection")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_create_collection_fail(mock_load_data_from_s3, mock_create_collection):

    # Configure test variables
    test_id = "test_id"
    test_key = f"transformed/catalog_key_1/{test_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": [],
        "added_keys": ["{test_key}"],
        "deleted_keys": [],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_id, "type": "Collection"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_create_collection.return_value = False  # cannot create collection so will try again

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_create_collection.call_count == 3
    # Ensure all three calls are identical
    calls = mock_create_collection.call_args_list
    for i in range(3):
        assert calls[i].args[0] == api_url
        assert calls[i].args[1] == test_id
        assert calls[i].args[2] == test_data
        assert calls[i].args[3] == test_catalog_path


@patch("stac_fastapi_ingester.__main__.update_collection")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_update_collection_success(
    mock_load_data_from_s3, mock_update_collection
):

    # Configure test variables
    test_id = "test_id"
    test_key = f"transformed/catalog_key_1/{test_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": ["{test_key}"],
        "added_keys": [],
        "deleted_keys": [],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_id, "type": "Collection"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_update_collection.return_value = True  # updated succesfully

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_update_collection.call_count == 1
    mock_update_collection.assert_called_once_with(api_url, test_id, test_data, test_catalog_path)


@patch("stac_fastapi_ingester.__main__.update_collection")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_update_collection_fail(mock_load_data_from_s3, mock_update_collection):

    # Configure test variables
    test_id = "test_id"
    test_key = f"transformed/catalog_key_1/{test_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": ["{test_key}"],
        "added_keys": [],
        "deleted_keys": [],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_id, "type": "Collection"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_update_collection.return_value = False  # cannot update collection so will try again

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_update_collection.call_count == 3
    # Ensure all three calls are identical
    calls = mock_update_collection.call_args_list
    for i in range(3):
        assert calls[i].args[0] == api_url
        assert calls[i].args[1] == test_id
        assert calls[i].args[2] == test_data
        assert calls[i].args[3] == test_catalog_path


@patch("stac_fastapi_ingester.__main__.delete_collection")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_delete_collection(mock_load_data_from_s3, mock_delete_collection):

    # Configure test variables
    test_id = "test_id"
    test_key = f"transformed/catalog_key_1/{test_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": [],
        "added_keys": [],
        "deleted_keys": ["{test_key}"],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_id, "type": "Collection"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_delete_collection.return_value = None

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_delete_collection.call_count == 1
    mock_delete_collection.assert_called_once_with(api_url, test_id, test_catalog_path)

    ########################################################################################


@patch("stac_fastapi_ingester.__main__.create_item")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_create_item_success(mock_load_data_from_s3, mock_create_item):

    # Configure test variables
    test_item_id = "item_key_1"
    test_collection_id = "collection_key_1"
    test_key = f"transformed/catalog_key_1/collection_key_1/{test_item_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": [],
        "added_keys": ["{test_key}"],
        "deleted_keys": [],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_item_id, "type": "Feature", "collection": "collection_key_1"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_create_item.return_value = True  # created succesfully

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_create_item.call_count == 1
    mock_create_item.assert_called_once_with(
        api_url, test_collection_id, test_item_id, test_data, test_catalog_path
    )


@patch("stac_fastapi_ingester.__main__.create_item")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_create_item_fail(mock_load_data_from_s3, mock_create_item):

    # Configure test variables
    test_item_id = "item_key_1"
    test_collection_id = "collection_key_1"
    test_key = f"transformed/catalog_key_1/collection_key_1/{test_item_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": [],
        "added_keys": ["{test_key}"],
        "deleted_keys": [],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_item_id, "type": "Feature", "collection": "collection_key_1"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_create_item.return_value = False  # cannot create item so will try again

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_create_item.call_count == 3
    # Ensure all three calls are identical
    calls = mock_create_item.call_args_list
    for i in range(3):
        assert calls[i].args[0] == api_url
        assert calls[i].args[1] == test_collection_id
        assert calls[i].args[2] == test_item_id
        assert calls[i].args[3] == test_data
        assert calls[i].args[4] == test_catalog_path


@patch("stac_fastapi_ingester.__main__.update_item")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_update_item_success(mock_load_data_from_s3, mock_update_item):

    # Configure test variables
    test_item_id = "item_key_1"
    test_collection_id = "collection_key_1"
    test_key = f"transformed/catalog_key_1/collection_key_1/{test_item_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": ["{test_key}"],
        "added_keys": [],
        "deleted_keys": [],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_item_id, "type": "Feature", "collection": "collection_key_1"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_update_item.return_value = True  # updated succesfully

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_update_item.call_count == 1
    mock_update_item.assert_called_once_with(
        api_url, test_collection_id, test_item_id, test_data, test_catalog_path
    )


@patch("stac_fastapi_ingester.__main__.update_item")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_update_item_fail(mock_load_data_from_s3, mock_update_item):

    # Configure test variables
    test_item_id = "item_key_1"
    test_collection_id = "collection_key_1"
    test_key = f"transformed/catalog_key_1/collection_key_1/{test_item_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": ["{test_key}"],
        "added_keys": [],
        "deleted_keys": [],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_item_id, "type": "Feature", "collection": "collection_key_1"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_update_item.return_value = False  # cannot update collection so will try again

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_update_item.call_count == 3
    # Ensure all three calls are identical
    calls = mock_update_item.call_args_list
    for i in range(3):
        assert calls[i].args[0] == api_url
        assert calls[i].args[1] == test_collection_id
        assert calls[i].args[2] == test_item_id
        assert calls[i].args[3] == test_data
        assert calls[i].args[4] == test_catalog_path


@patch("stac_fastapi_ingester.__main__.delete_item")
@patch("stac_fastapi_ingester.__main__.load_data_from_s3")
def test_interpret_message_delete_item(mock_load_data_from_s3, mock_delete_item):

    # Configure test variables
    test_item_id = "item_key_1"
    test_collection_id = "collection_key_1"
    test_key = f"transformed/catalog_key_1/collection_key_1/{test_item_id}"
    test_catalog_path = "catalog_key_1"
    test_msg = f"""{{
        "id": "pulsar-test-id/testing",
        "workspace": "",
        "repository": "",
        "branch": "main",
        "bucket_name": "test-bucket",
        "updated_keys": [],
        "added_keys": [],
        "deleted_keys": ["{test_key}"],
        "source": "https://test-catalog.temp.data.com",
        "target": "test-datasets/test-catalog"
    }}"""

    api_url = "https://test-url/api"

    test_data = {"id": test_item_id, "type": "Feature", "collection": "collection_key_1"}

    # Configure mocks
    mock_load_data_from_s3.return_value = test_data
    mock_delete_item.return_value = None

    # Call function
    interpret_message(test_msg, api_url)

    # Check function called as expected
    assert mock_delete_item.call_count == 1
    mock_delete_item.assert_called_once_with(
        api_url, test_collection_id, test_item_id, test_catalog_path
    )


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
