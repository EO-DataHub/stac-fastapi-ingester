import json
import logging
from unittest import mock
from unittest.mock import patch

import pytest
import requests
from requests import Response

from stac_fastapi_ingester.errors import InvalidSTACException, SFAPIConnectionError
from stac_fastapi_ingester.handle_changes import (
    create_or_update_entry,
    delete_entry,
    handle_access_policy,
    update_entry_access_policy,
)


@pytest.mark.parametrize(
    "data_type",
    [
        ("Catalog"),
        ("Collection"),
        ("Feature"),
    ],
)
@patch("stac_fastapi_ingester.handle_changes.log_response")
def test_create_or_update_entry_create(mock_log_response, data_type, requests_mock):
    """
    Test the create_or_update_entry method when creating new entry.
    """
    # Set variables
    api_url = "https://test-url/api"
    entry_id = "catalog_id"
    data = {"type": data_type, "id": entry_id}
    workspace = "test-workspace"
    catalog_path = "test/path"
    new_catalog_path = "test"

    # Configure mocks
    requests_mock.put(f"{api_url}/{catalog_path}", status_code=404, json={"message": "Entry Doesn't Exist"})
    requests_mock.post(f"{api_url}/{new_catalog_path}", status_code=200, json={"message": "Entry Created"})
    mock_log_response.return_value = None

    create_or_update_entry(api_url, data, workspace, catalog_path)

    # Assertions
    log_history = mock_log_response.mock_calls

    # Check first log call
    assert isinstance(log_history[0][1][0], Response)
    assert log_history[0][1][0].status_code == 404
    assert log_history[0][1][0].json() == {"message": "Entry Doesn't Exist"}
    assert log_history[0][1][1] == entry_id
    assert log_history[0][1][2] == catalog_path
    assert log_history[0][1][3] == api_url
    assert log_history[0][1][4] == data_type

    # Check second log call
    assert isinstance(log_history[1][1][0], Response)
    assert log_history[1][1][0].status_code == 200
    assert log_history[1][1][0].json() == {"message": "Entry Created"}
    assert log_history[1][1][1] == entry_id
    assert log_history[1][1][2] == new_catalog_path
    assert log_history[1][1][3] == api_url
    assert log_history[1][1][4] == data_type


@pytest.mark.parametrize(
    "data_type",
    [
        ("Catalog"),
        ("Collection"),
        ("Feature"),
    ],
)
@patch("stac_fastapi_ingester.handle_changes.log_response")
def test_create_or_update_entry_update(mock_log_response, data_type, requests_mock):
    """
    Test the create_or_update_entry method when updating entry.
    """
    # Set variables
    api_url = "https://test-url/api"
    entry_id = "catalog_id"
    data = {"type": data_type, "id": entry_id}
    workspace = "test-workspace"
    catalog_path = "test/path"

    # Configure mocks
    requests_mock.put(f"{api_url}/{catalog_path}", status_code=200, json={"message": "Entry Updated Successfully"})
    mock_log_response.return_value = None

    create_or_update_entry(api_url, data, workspace, catalog_path)

    # Assertions
    log_history = mock_log_response.mock_calls
    assert isinstance(log_history[0][1][0], Response)
    assert log_history[0][1][0].status_code == 200
    assert log_history[0][1][0].json() == {"message": "Entry Updated Successfully"}
    assert log_history[0][1][1] == entry_id
    assert log_history[0][1][2] == catalog_path
    assert log_history[0][1][3] == api_url
    assert log_history[0][1][4] == data_type


@patch("stac_fastapi_ingester.handle_changes.log_response")
def test_create_or_update_entry_wrong_data_type(mock_log_response, requests_mock):
    """
    Test the create_or_update_entry method with wrong STAC data type.
    """
    # Set variables
    api_url = "https://test-url/api"
    data_type = "invalid-type"
    entry_id = "catalog_id"
    data = {"type": data_type, "id": entry_id}
    workspace = "test-workspace"
    catalog_path = "test/path"

    # Configure mocks
    requests_mock.put(f"{api_url}/{catalog_path}", status_code=200, json={"message": "Entry Updated Successfully"})
    mock_log_response.return_value = None

    with pytest.raises(InvalidSTACException):
        create_or_update_entry(api_url, data, workspace, catalog_path)

    # Assertions
    mock_log_response.assert_not_called()
    assert len(requests_mock.request_history) == 0


@patch("stac_fastapi_ingester.handle_changes.log_response")
def test_create_or_update_entry_missing_id(mock_log_response, requests_mock):
    """
    Test the create_or_update_entry method with missing ID.
    """
    # Set variables
    api_url = "https://test-url/api"
    data_type = "Catalog"
    data = {"type": data_type}
    workspace = "test-workspace"
    catalog_path = "test/path"

    # Configure mocks
    requests_mock.put(f"{api_url}/{catalog_path}", status_code=200, json={"message": "Entry Updated Successfully"})
    mock_log_response.return_value = None

    with pytest.raises(InvalidSTACException):
        create_or_update_entry(api_url, data, workspace, catalog_path)

    # Assertions
    mock_log_response.assert_not_called()
    assert len(requests_mock.request_history) == 0


@patch("stac_fastapi_ingester.handle_changes.log_response")
@patch("requests.put")
def test_create_or_update_entry_connection_error(mock_requests_put, mock_log_response):
    """
    Test the create_or_update_entry method when failing to connect to API.
    """
    # Set variables
    api_url = "https://test-url/api"
    data_type = "Catalog"
    entry_id = "catalog_id"
    data = {"type": data_type, "id": entry_id}
    workspace = "test-workspace"
    catalog_path = "test/path"

    # Configure mocks
    mock_requests_put.side_effect = requests.ConnectionError("Connection Error")
    mock_log_response.return_value = None

    with pytest.raises(SFAPIConnectionError):
        create_or_update_entry(api_url, data, workspace, catalog_path)

    # Assertions
    mock_log_response.assert_not_called()
    mock_requests_put.assert_called_once_with(
        f"{api_url}/{catalog_path}",
        headers={"accept": "application/json", "Content-Type": "application/json"},
        json=data,
        params={"workspace": workspace},
    )


@pytest.mark.parametrize(
    "data_type",
    [
        ("Catalog"),
        ("Collection"),
        ("Feature"),
    ],
)
@patch("stac_fastapi_ingester.handle_changes.log_response_delete")
def test_delete_entry(mock_log_response_delete, data_type, requests_mock):
    """
    Test the delete_entry method.
    """
    # Set variables
    api_url = "https://test-url/api"
    workspace = "test-workspace"
    catalog_path = "test/path"

    # Configure mocks
    requests_mock.delete(f"{api_url}/{catalog_path}", status_code=204, json={"message": "Entry Deleted Successfully"})
    mock_log_response_delete.return_value = None

    result = delete_entry(api_url, workspace, catalog_path)

    # Assertions
    log_history = mock_log_response_delete.mock_calls
    assert isinstance(log_history[0][1][0], Response)
    assert not result
    # First argument is confrimed to be a Response above
    mock_log_response_delete.assert_called_once_with(mock.ANY, catalog_path, api_url)


@patch("stac_fastapi_ingester.handle_changes.log_response_delete")
@patch("requests.delete")
def test_delete_entry_connection_error(mock_requests_delete, mock_log_response_delete):
    """
    Test the delete_entry method fails to connect to API.
    """
    # Set variables
    api_url = "https://test-url/api"
    workspace = "test-workspace"
    catalog_path = "test/path"

    # Configure mocks
    mock_requests_delete.side_effect = requests.ConnectionError("Connection Error")
    mock_log_response_delete.return_value = None

    with pytest.raises(SFAPIConnectionError):
        delete_entry(api_url, workspace, catalog_path)

    # Assertions
    mock_requests_delete.assert_called_once_with(
        f"{api_url}/{catalog_path}",
        headers={"accept": "application/json"},
        params={"workspace": workspace},
    )


def test_update_entry_access_policy(requests_mock, caplog):
    """
    Test the update_entry_access_policy method.
    """

    # Set logging level
    caplog.set_level(logging.INFO)

    # Set variables
    api_url = "https://test-url/api"
    path = "path/to/entry"
    policy = {"path": path, "access": {"public": True}}
    workspace = "test-workspace"

    # Configure mocks
    requests_mock.put(
        f"{api_url}/{path}/access-policy",
        status_code=204,
        json={"message": "Entry Deleted Successfully"},
    )

    update_entry_access_policy(api_url, policy, workspace)

    # Assertions
    assert f"Updated access control for data at {path}" in caplog.text


def test_update_entry_access_policy_not_found(requests_mock, caplog):
    """
    Test the update_entry_access_policy method when entry is not found in Catalogue.
    """

    # Set logging level
    caplog.set_level(logging.INFO)

    # Set variables
    api_url = "https://test-url/api"
    path = "path/to/entry"
    policy = {"path": path, "access": {"public": True}}
    workspace = "test-workspace"

    # Configure mocks
    requests_mock.put(
        f"{api_url}/{path}/access-policy",
        status_code=404,
        json={"message": "Entry Failed to Delete"},
    )

    update_entry_access_policy(api_url, policy, workspace)

    # Assertions
    assert f"Failed to update access control for data at {path}" in caplog.text


@patch("requests.put")
def test_update_entry_access_policy_connection_error(mock_requests_put, caplog):
    """
    Test the update_entry_access_policy method when failing to connect to API.
    """

    # Set logging level
    caplog.set_level(logging.INFO)

    # Set variables
    api_url = "https://test-url/api"
    path = "path/to/entry"
    policy = {"path": path, "access": {"public": True}}
    workspace = "test-workspace"

    # Configure mocks
    mock_requests_put.side_effect = requests.ConnectionError("Connection Error")

    with pytest.raises(SFAPIConnectionError):
        update_entry_access_policy(api_url, policy, workspace)

    # Assertions
    assert f"Access Policy: {path} not updated" in caplog.text
    mock_requests_put.assert_called_once_with(
        f"{api_url}/{path}/access-policy",
        headers={"accept": "application/json", "Content-Type": "application/json"},
        data=json.dumps(policy["access"]),
        params={"workspace": workspace},
    )


@patch("stac_fastapi_ingester.handle_changes.update_entry_access_policy")
def test_handle_access_policy(mock_update_entry_access_policy):
    """
    Test the handle_access_policy method.
    """

    # Set variables
    api_url = "https://test-url/api"
    workspace = "test-workspace"
    policy_1 = {
        "path": "path/to/another/entry",
        "access": {"public": True},
    }
    policy_2 = {
        "path": "path/to/entry",
        "access": {"public": False},
    }

    data = {
        "policies": [
            policy_1,
            policy_2,
        ]
    }

    # Configure mocks
    mock_update_entry_access_policy.return_value = None

    # Call the function
    handle_access_policy(api_url, data, workspace)

    # Assertions
    calls = mock_update_entry_access_policy.mock_calls
    assert len(calls) == 2
    assert calls[0][1][0] == api_url
    assert calls[0][1][1] == policy_2  # shorter path parsed first
    assert calls[0][1][2] == workspace
    assert calls[1][1][0] == api_url
    assert calls[1][1][1] == policy_1
    assert calls[1][1][2] == workspace
