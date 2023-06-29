import gzip
import json
import logging
import os
import re
import sys
from glob import glob
from io import BytesIO
from pathlib import Path

import backoff
import boto3
import requests
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

logger = logging.getLogger("inframock")
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
out_hdlr.setLevel(logging.DEBUG)
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)

POPULATE_MOCK = os.getenv("POPULATE_MOCK")
AWS_ACCOUNT_ID = "000000000000"

# data is always mounted into /data regardless of the origin location
DATA_LOCATION = "/data"
ENVIROMENT = "development"
LOCALSTACK_ENDPOINT = "http://localstack:4566"
SOURCE_BUCKET_NAME = f"biomage-source-development-{AWS_ACCOUNT_ID}"
PROCESSED_MATRIX_BUCKET_NAME = f"processed-matrix-development-{AWS_ACCOUNT_ID}"
CELL_SETS_BUCKET_NAME = f"cell-sets-development-{AWS_ACCOUNT_ID}"
MB = 1024 ** 2
config = TransferConfig(multipart_threshold=20 * MB)


@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_time=60)
def wait_for_localstack():
    logger.info("Waiting for localstack to spin up...")
    requests.get(LOCALSTACK_ENDPOINT)


def get_experiments():
    return [
        d
        for d in os.listdir(DATA_LOCATION)
        if os.path.isdir(os.path.join(DATA_LOCATION, d))
    ]


def provision_biomage_stack():
    def stack_name(resource):
        return f"biomage-{resource}-development"

    cf = boto3.client("cloudformation", endpoint_url=LOCALSTACK_ENDPOINT)
    logger.info(
        "Expect harmless error on localstack.services.sns.sns_listener if the API is not running"
    )
    resources = ("sns", "s3-v2")
    for resource in resources:
        path = f"https://raw.githubusercontent.com/hms-dbmi-cellenics/iac/master/cf/{resource}.yaml"

        response = requests.get(path)
        template = response.text
        name = stack_name(resource)

        logger.info(f"Creating stack {name}...")
        try:
            cf.create_stack(
                StackName=name,
                TemplateBody=template,
                Parameters=[
                    {
                        "ParameterKey": "Environment",
                        "ParameterValue": "development",
                    },
                ],
            )
        except ClientError as e:
            logger.info(e.response["Error"]["Message"])
            if "already exists" not in e.response["Error"]["Message"]:
                raise

    logger.info("Waiting for stacks creation to complete...")
    waiter = cf.get_waiter("stack_create_complete")
    for resource in resources:
        name = stack_name(resource)
        waiter.wait(StackName=name)
        logger.info(f"Stack {name} created.")

    sns = boto3.client("sns", endpoint_url=LOCALSTACK_ENDPOINT)
    logger.info("SNS topics: %s" % sns.list_topics()["Topics"])
    logger.info("SNS subscriptions: %s" % sns.list_subscriptions()["Subscriptions"])


def handle_file(experiment_id, f):
    # handle file will:
    # * update S3 for data files named r.rds.gz
    # * ignore the file otherwise
    filename = Path(f).name
    logger.info(f" - {filename}")

    if re.match("^biomage-source.r.rds.gz$", filename):
        update_S3_count_matrix(experiment_id, f, SOURCE_BUCKET_NAME)
        logger.info(f"\t{filename} data successfully uploaded to S3.")

    elif re.match("^processed-matrix.r.rds.gz$", filename):
        update_S3_count_matrix(experiment_id, f, PROCESSED_MATRIX_BUCKET_NAME)
        logger.info(f"\t{filename} data successfully uploaded to S3.")

    elif re.match("^mock_cell_sets.json$", filename):
        update_S3_cell_sets(experiment_id, f)
        logger.info(f"\t{filename} data successfully uploaded to S3.")

    else:
        logger.warning(f"\tUnknown input file {filename}, continuing")


def update_S3_count_matrix(experiment_id, f, bucket_name):
    with open(f, mode="rb") as r:
        r.raw.decode_content = True
        contents = gzip.GzipFile(fileobj=r.raw, mode="rb")

        s3 = boto3.resource("s3", endpoint_url=LOCALSTACK_ENDPOINT)

        s3.Object(
            bucket_name,
            f"{experiment_id}/r.rds",
        ).upload_fileobj(Fileobj=contents, Config=config)


def update_S3_cell_sets(experiment_id, f):
    with open(f, mode="rb") as file_handle:

        buf = BytesIO(file_handle.read())

        s3 = boto3.resource("s3", endpoint_url=LOCALSTACK_ENDPOINT)

        s3.Object(CELL_SETS_BUCKET_NAME, f"{experiment_id}").upload_fileobj(
            Fileobj=buf, Config=config
        )


def populate_localstack():
    for experiment_id in get_experiments():
        logger.info(f"Loading data for {experiment_id}:")

        # for each S3 file in the experiment current folder either upload it to localstack
        for f in glob(f"{DATA_LOCATION}/{experiment_id}/*"):
            handle_file(experiment_id, f)


def main():
    logger.info(
        "InfraMock local service started. Waiting for LocalStack to be brought up..."
    )

    wait_for_localstack()

    logger.info("LocalStack is up. Provisioning Biomage stack...")
    provision_biomage_stack()

    if POPULATE_MOCK == "true":
        logger.info("Going to populate mock S3 with experiment data.")
        populate_localstack()

    region = os.getenv("AWS_DEFAULT_REGION")
    logger.info("*" * 80)
    logger.info(f"InfraMock is RUNNING in mocked region {region}")
    logger.info("Check `docker-compose.yaml` for ports to acces services.")
    logger.info("Any other questions? Read the README, or ask on #engineering.")
    logger.info("*" * 80)


if __name__ == "__main__":
    main()
