import os
from unittest import mock
from unittest.mock import patch

from click.testing import CliRunner

from stac_fastapi_ingester.__main__ import main

##############
## Test CLI ##
##############


@patch.dict(os.environ, {"FASTAPI_URL": "https://test-url/api"})
@patch("stac_fastapi_ingester.__main__.setup_logging")
@patch("stac_fastapi_ingester.__main__.log_component_version")
@patch("stac_fastapi_ingester.__main__.run")
@patch("stac_fastapi_ingester.__main__.get_boto3_session")
@patch("stac_fastapi_ingester.__main__.IngesterMessager")
def test_cli_with_topic_and_pulsar_url(
    mock_Ingester_Messager,
    mock_get_boto3_session,
    mock_run,
    mock_log_component_version,
    mock_setup_logging,
    caplog,
):

    # Configure mocks
    mock_s3_client = mock.Mock()
    mock_boto3_session = mock.Mock()
    mock_boto3_session.client.return_value = mock_s3_client
    mock_get_boto3_session.return_value = mock_boto3_session

    mock_ingester_messager = mock.Mock(api_url="https://test-url/api")
    mock_Ingester_Messager.return_value = mock_ingester_messager

    mock_run.return_value = None

    # Set up the CliRunner
    runner = CliRunner()

    # Invoke the CLI with a test topic
    result = runner.invoke(main, ["test-topic", "--prefix", "test_name"])

    # Assertions
    # Check the CLI ran successfully
    assert result.exit_code == 0

    # Check the Pulsar calls and response
    mock_setup_logging.assert_called_once_with(verbosity=0)
    mock_log_component_version.assert_called_once_with("stac-fastapi-ingester")
    mock_get_boto3_session.assert_called_once()

    # Check message is received correctly
    mock_run.assert_called_once_with(
        {"test-topic": mock_ingester_messager}, subscription_name="test_name", threads=1
    )


@patch.dict(os.environ, {"FASTAPI_URL": "https://test-url/api"})
@patch("stac_fastapi_ingester.__main__.setup_logging")
@patch("stac_fastapi_ingester.__main__.log_component_version")
@patch("stac_fastapi_ingester.__main__.run")
@patch("stac_fastapi_ingester.__main__.get_boto3_session")
@patch("stac_fastapi_ingester.__main__.IngesterMessager")
def test_cli_with_topic_and_pulsar_url_test_args(
    mock_Ingester_Messager,
    mock_get_boto3_session,
    mock_run,
    mock_log_component_version,
    mock_setup_logging,
    caplog,
):

    # Configure mocks
    mock_s3_client = mock.Mock()
    mock_boto3_session = mock.Mock()
    mock_boto3_session.client.return_value = mock_s3_client
    mock_get_boto3_session.return_value = mock_boto3_session

    mock_ingester_messager = mock.Mock(api_url="https://test-url/api")
    mock_Ingester_Messager.return_value = mock_ingester_messager

    mock_run.return_value = None

    # Set up the CliRunner
    runner = CliRunner()

    # Invoke the CLI with a test topic
    result = runner.invoke(main, ["test-topic", "-t", 5, "-p", "test_name", "-v", "-v"])

    # Assertions
    # Check the CLI ran successfully
    assert result.exit_code == 0

    # Check the Pulsar calls and response
    mock_setup_logging.assert_called_once_with(verbosity=2)
    mock_log_component_version.assert_called_once_with("stac-fastapi-ingester")
    mock_get_boto3_session.assert_called_once()

    # Check message is received correctly
    mock_run.assert_called_once_with(
        {"test-topic": mock_ingester_messager}, subscription_name="test_name", threads=5
    )


@patch.dict(os.environ, {"FASTAPI_URL": "https://test-url/api"})
@patch("stac_fastapi_ingester.__main__.setup_logging")
@patch("stac_fastapi_ingester.__main__.log_component_version")
@patch("stac_fastapi_ingester.__main__.run")
@patch("stac_fastapi_ingester.__main__.get_boto3_session")
@patch("stac_fastapi_ingester.__main__.IngesterMessager")
def test_cli_with_missing_api_url(
    mock_Ingester_Messager,
    mock_get_boto3_session,
    mock_run,
    mock_log_component_version,
    mock_setup_logging,
    caplog,
):

    # Configure mocks
    mock_s3_client = mock.Mock()
    mock_boto3_session = mock.Mock()
    mock_boto3_session.client.return_value = mock_s3_client
    mock_get_boto3_session.return_value = mock_boto3_session

    mock_ingester_messager = mock.Mock(api_url=None)
    mock_Ingester_Messager.return_value = mock_ingester_messager

    mock_run.return_value = None

    # Set up the CliRunner
    runner = CliRunner()

    # Invoke the CLI with a test topic
    result = runner.invoke(main, ["test-topic", "-t", 5, "-p", "test_name", "-v", "-v"])

    # Assertions
    # Check the CLI ran successfully
    assert result.exit_code == 1
    assert "STAC-FastApi URL must be provided in the environment variable 'FASTAPI_URL'" in str(
        result.exception
    )

    # Check the Pulsar calls and response
    mock_setup_logging.assert_called_once_with(verbosity=2)
    mock_log_component_version.assert_called_once_with("stac-fastapi-ingester")
    mock_get_boto3_session.assert_called_once()

    # Check message is received correctly
    mock_run.assert_not_called()
