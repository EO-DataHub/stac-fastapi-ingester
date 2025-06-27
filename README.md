# stac-fastapi-ingester

An ingester to load STAC Catalogs, Collections and Items into STAC-Fastapi, read from S3 bucket, triggered by Pulsar messages. This application uses the Messagers class defined in the [eodhp-utils](https://github.com/EO-DataHub/eodhp-utils) package, to handle Pulsar messaging via Actions.

## How to use this repository

First install the dependencies by running `pip install -r requirements.txt`, for development work also install `pip install -r requirements-dev.txt`.
We can now test the ingester with Pulsar messaging.  
These instructions assume that a Pulsar client is running on a local port, this can also be forwarded from a remote cluster. An example of this can be found in the [eodhp-argocd-deployment](https://github.com/UKEODHP/eodhp-argocd-deployment) repository using the running EODHP Pulsar client. With the port forwarding active, we now need to configure our environment variables to specify the Pulsar and Fastapi URLs. Do this by running the following

```console
export FASTAPI_URL=<fastapi_url>
export PULSAR_URL=<pulsar_url>
```

You can then initiate the subscriber module by running the following command `python -m stac-fastapi-ingester <topic> subscribe  --prefix <subscriber_name>` for example to listen to the `transformed` topic with the subscriber_name `fastapi` run `python -m stac-fastapi-ingester transformed subscribe  --prefix test`. This module is now listening for messages on the `transformed` topic which will then trigger loading of data into STAC Fastapi.

To test the messaging service correctly triggers the ingestion, open a new terminal and use the provided stac-fastapi-pulsar-test.py script to send a test message via Pulsar. To do this, configure the test message on lines 40-47 to define which files you with to ingest, **do not change the dictionary keys**. Next run this script using command `python stac-fastapi-pulsar-test.py <topic> publish --prefix pub1 -n 1`. This will send a single message via Pulsar to initiate the ingestion of the provided data. E.g. to trigger the previous subscriber run `python stac-fastapi-pulsar-test.py pulsar://127.0.0.1:6650 transformed publish --prefix pub1 -n 1`, make sure the `PULSAR_URL` environment variable is set in this terminal too.

Once this message is sent you can return to the subscriber terminal and see the logging outputs for the data being loaded. This default script will ingest some CMIP6 and Cordex data, update one of the CMIP6 files and then delete the Cordex collection. You can check the ingestion by visiting [https://eodatahub.org.uk/api/catalogue/stac/api.html](https://eodatahub.org.uk/stac-fastapi/api.html).

# Install via makefile

```commandline
make setup
```

This will create a virtual environment called `venv`, build `requirements.txt` and
`requirements-dev.txt` from `pyproject.toml` if they're out of date, install the Python
and Node dependencies and install `pre-commit`.

It's safe and fast to run `make setup` repeatedly as it will only update these things if
they have changed.

After `make setup` you can run `pre-commit` to run pre-commit checks on staged changes and
`pre-commit run --all-files` to run them on all files. This replicates the linter checks that
run from GitHub actions.

# Install via makefile

```commandline
make setup
```

This will create a virtual environment called `venv`, build `requirements.txt` and
`requirements-dev.txt` from `pyproject.toml` if they're out of date, install the Python
and Node dependencies and install `pre-commit`.

It's safe and fast to run `make setup` repeatedly as it will only update these things if
they have changed.

After `make setup` you can run `pre-commit` to run pre-commit checks on staged changes and
`pre-commit run --all-files` to run them on all files. This replicates the linter checks that
run from GitHub actions.
