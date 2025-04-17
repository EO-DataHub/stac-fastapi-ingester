from typing import Optional

import click
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

    # Configure S3 client
    s3_client = get_boto3_session().client("s3")

    ingester_messager = IngesterMessager(
        s3_client=s3_client,
    )

    if not ingester_messager.api_url:
        raise Exception(
            "STAC-FastApi URL must be provided in the environment variable 'FASTAPI_URL'"
        )

    run(
        {topic: ingester_messager},
        subscription_name=prefix,
        threads=threads,
    )


if __name__ == "__main__":
    main()
