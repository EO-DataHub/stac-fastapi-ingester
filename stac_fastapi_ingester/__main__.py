import logging
import os
import time
from typing import Optional

import click
import requests
from eodhp_utils.runner import (
    get_boto3_session,
    log_component_version,
    run,
    setup_logging,
)

from .ingester_messager import IngesterMessager


@click.command()
@click.argument("topic", type=str)
@click.option("-v", "--verbose", count=True)
@click.option("-t", "--threads", type=int, default=1)
@click.option("-p", "--prefix", type=str, default=None)
def main(topic: str, verbose: int, threads: int, prefix: Optional[str]):
    """
    Subscribe to messages from a Pulsar broker.
    """
    setup_logging(verbosity=verbose)
    log_component_version("stac-fastapi-ingester")

    # Check STAC-FastApi is running
    api_url = os.getenv("FASTAPI_URL", "")
    if not api_url:
        raise Exception(
            "STAC-FastApi URL must be provided in the environment variable 'FASTAPI_URL'"
        )
    retry = True
    while True:
        try:
            response = requests.get(
                f"{api_url}",
            )
            retry = True
            if response.status_code == 200:
                retry = False
        except requests.ConnectionError:
            retry = True
        if not retry:
            break
        logging.warning("STAC-FastApi is not yet available, retrying in 10 seconds...")
        time.sleep(10)

    logging.info("STAC-FastApi is available, starting ingester...")

    # Configure S3 client
    s3_client = get_boto3_session().client("s3")

    ingester_messager = IngesterMessager(
        s3_client=s3_client,
    )

    run(
        {topic: ingester_messager},
        subscription_name=prefix,
        threads=threads,
    )


if __name__ == "__main__":
    main()
