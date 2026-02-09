import os
from unittest.mock import patch

import pytest

from stac_fastapi_ingester.ingester_messager import IngesterMessager


@pytest.fixture
@patch.dict(os.environ, {"FASTAPI_URL": "https://test-url/api"})
def ingester_messager():
    """
    Fixture to mock the IngesterMessager class.
    """
    ingester_messager = IngesterMessager()
    ingester_messager.input_change_msg = {"workspace": "test_workspace"}
    return ingester_messager


@patch.dict(os.environ, {"FASTAPI_URL": "https://test-url/api"})
def test_api_url_is_set_on_instantiation():
    """
    Test that the api_url is set correctly on instantiation of IngesterMessager.
    """
    # Instantiate the class
    ingester_messager = IngesterMessager()

    # Assert that api_url is set correctly
    assert ingester_messager.api_url == "https://test-url/api"


@patch("stac_fastapi_ingester.ingester_messager.create_or_update_entry")
def test_process_update_body_stac(mock_create_or_update_entry, ingester_messager):
    """
    Test the process_update_body method of the IngesterMessager class when handling STAC.
    """
    # Mock the necessary components
    mock_create_or_update_entry.return_value = None

    # Define test inputs
    entry_body = {"key": "value"}
    cat_path = "test/path.json"
    source = "source"
    target = "target"

    # Call the method
    result = ingester_messager.process_update_body(entry_body, cat_path, source, target)

    # Assertions
    assert result == []
    mock_create_or_update_entry.assert_called_once_with(
        "https://test-url/api", entry_body, "test_workspace", "test/path"
    )


@patch("stac_fastapi_ingester.ingester_messager.handle_access_policy")
def test_process_update_body_access_policy(mock_handle_access_policy, ingester_messager):
    """
    Test the process_update_body method of the IngesterMessager class when handling access-policies.
    """
    # Mock the necessary components
    mock_handle_access_policy.return_value = None

    # Define test inputs
    entry_body = {"key": "value"}
    cat_path = "test/path/meta_access_policy.json"
    source = "source"
    target = "target"

    # Call the method
    result = ingester_messager.process_update_body(entry_body, cat_path, source, target)

    # Assertions
    assert result == []
    mock_handle_access_policy.assert_called_once_with("https://test-url/api", entry_body, "test_workspace")


@patch("stac_fastapi_ingester.ingester_messager.delete_entry")
def test_process_delete(mock_delete_entry, ingester_messager):
    """
    Test the process_delete method of the IngesterMessager class.
    """
    # Mock the necessary components
    mock_delete_entry.return_value = None

    # Define test inputs
    input_bucket = "test-bucket"
    input_key = "test-key"
    cat_path = "test/path.json"
    source = "source"
    target = "target"

    # Call the method
    result = ingester_messager.process_delete(input_bucket, input_key, cat_path, source, target)

    # Assertions
    assert result == []
    mock_delete_entry.assert_called_once_with("https://test-url/api", "test_workspace", "test/path")
