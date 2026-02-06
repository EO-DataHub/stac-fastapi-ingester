# stac-fastapi-ingester

An ingester to load STAC Catalogs, Collections and Items into STAC-Fastapi, read from S3 bucket, triggered by Pulsar messages. This application uses the Messagers class defined in the [eodhp-utils](https://github.com/EO-DataHub/eodhp-utils) package, to handle Pulsar messaging via Actions.

## How to use this repository

First install the dependencies by running `make setup`.
We can now test the ingester with Pulsar messaging.
These instructions assume that a Pulsar client is running on a local port, this can also be forwarded from a remote cluster. An example of this can be found in the [eodhp-argocd-deployment](https://github.com/UKEODHP/eodhp-argocd-deployment) repository using the running EODHP Pulsar client. With the port forwarding active, we now need to configure our environment variables to specify the Pulsar and Fastapi URLs. Do this by running the following

```console
export FASTAPI_URL=<fastapi_url>
export PULSAR_URL=<pulsar_url>
```

You can then initiate the subscriber module by running the following command `python -m stac-fastapi-ingester <topic> subscribe  --prefix <subscriber_name>` for example to listen to the `transformed` topic with the subscriber_name `fastapi` run `python -m stac-fastapi-ingester transformed subscribe  --prefix test`. This module is now listening for messages on the `transformed` topic which will then trigger loading of data into STAC Fastapi.

To test the messaging service correctly triggers the ingestion, open a new terminal and use the provided stac-fastapi-pulsar-test.py script to send a test message via Pulsar. To do this, configure the test message on lines 40-47 to define which files you with to ingest, **do not change the dictionary keys**. Next run this script using command `python stac-fastapi-pulsar-test.py <topic> publish --prefix pub1 -n 1`. This will send a single message via Pulsar to initiate the ingestion of the provided data. E.g. to trigger the previous subscriber run `python stac-fastapi-pulsar-test.py pulsar://127.0.0.1:6650 transformed publish --prefix pub1 -n 1`, make sure the `PULSAR_URL` environment variable is set in this terminal too.

Once this message is sent you can return to the subscriber terminal and see the logging outputs for the data being loaded. This default script will ingest some CMIP6 and Cordex data, update one of the CMIP6 files and then delete the Cordex collection. You can check the ingestion by visiting [https://eodatahub.org.uk/api/catalogue/stac/api.html](https://eodatahub.org.uk/stac-fastapi/api.html).

## Development setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```commandline
make setup
```

This will install all dependencies (including dev dependencies) via `uv sync` and set up `pre-commit` hooks.

It's safe and fast to run `make setup` repeatedly as it will only update things if they have changed.

### Available make targets

- `make setup` - Install dependencies and pre-commit hooks
- `make test` - Run tests in watch mode
- `make testonce` - Run tests once
- `make format` - Auto-format code with ruff
- `make check` - Run all linting and type checks (ruff, pyright, validate-pyproject)
- `make pre-commit` - Run pre-commit checks on staged changes
- `make pre-commit-all` - Run pre-commit checks on all files
- `make dockerbuild` - Build Docker image
- `make dockerpush` - Build and push Docker image
