import gzip
import logging
import os
import re
import sys
from glob import glob
from pathlib import Path

import backoff
import boto3
import requests
import simplejson as json
from boto3.s3.transfer import TransferConfig

logger = logging.getLogger("inframock")
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
out_hdlr.setLevel(logging.DEBUG)
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)

POPULATE_MOCK = os.getenv("POPULATE_MOCK")

# data is always mounted into /data regardless of the origin location
DATA_LOCATION = "/data"
ENVIROMENT = "development"
LOCALSTACK_ENDPOINT = "http://localstack:4566"
SOURCE_BUCKET_NAME = "biomage-source-development"
MB = 1024 ** 2
config = TransferConfig(multipart_threshold=20 * MB)


@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_time=60)
def wait_for_localstack():
    logger.info("Waiting for localstack to spin up...")
    requests.get(LOCALSTACK_ENDPOINT)


def get_file_table(filename):
    if re.match("mock_experiment.*.json", filename):
        return "experiments"

    if re.match("mock_samples.*.json", filename):
        return "samples"

    if re.match("mock_plots_tables.*.json", filename):
        return "plots-tables"

    # this should not be reachable as the names a prefiltered in handle_file()
    raise ValueError(f"invalid file provided {filename}")


def get_experiments():
    return [
        d
        for d in os.listdir(DATA_LOCATION)
        if os.path.isdir(os.path.join(DATA_LOCATION, d))
    ]


def provision_biomage_stack():
    resources = ("dynamo", "s3", "sns")

    cf = boto3.resource("cloudformation", endpoint_url=LOCALSTACK_ENDPOINT)

    for r in resources:
        path = f"https://raw.githubusercontent.com/biomage-ltd/iac/master/cf/{r}.yaml"

        r = requests.get(path)
        stack_template = r.text

        stack = cf.create_stack(
            StackName=f"biomage-{r}-development",
            TemplateBody=stack_template,
            Parameters=[
                {
                    "ParameterKey": "Environment",
                    "ParameterValue": "development",
                },
            ],
        )

    sns = boto3.client("sns", endpoint_url=LOCALSTACK_ENDPOINT)

    logger.info(sns.list_topics())

    logger.info("Stack created.")
    return stack


def handle_file(experiment_id, f):
    # handle file will:
    # * update DynamoDB for files matching mock_*.json
    # * update S3 for data files named r.rds.gz
    # * ignore the file otherwise
    filename = Path(f).name
    logger.info(f" - {filename}")

    if re.match("mock_.*.json", filename):
        update_dynamoDB(f)
        logger.info(f"\tMocked {filename} loaded into local DynamoDB.")

    elif re.match("r.rds.gz", filename):
        update_S3(experiment_id, f)
        logger.info("\tMocked experiment data successfully uploaded to S3.")

    else:
        logger.warning(f"\tUnknown input file {filename}, continuing")


def update_dynamoDB(f):
    filename = Path(f).name
    with open(f) as json_file:
        table_name = get_file_table(filename)

        data = json.load(json_file, use_decimal=True)

        dynamo = boto3.resource("dynamodb", endpoint_url=LOCALSTACK_ENDPOINT)
        table = dynamo.Table("{}-{}".format(table_name, ENVIROMENT))

        if data.get("records"):
            for data_item in data["records"]:
                table.put_item(Item=data_item)
        else:
            table.put_item(Item=data)


def update_S3(experiment_id, f):
    with open(f, mode="rb") as r:
        r.raw.decode_content = True
        contents = gzip.GzipFile(fileobj=r.raw, mode="rb")

        s3 = boto3.resource("s3", endpoint_url=LOCALSTACK_ENDPOINT)

        s3.Object(
            SOURCE_BUCKET_NAME,
            f"{experiment_id}/{Path(f).stem}",
        ).upload_fileobj(Fileobj=contents, Config=config)


def populate_localstack():
    for experiment_id in get_experiments():
        logger.info(f"Loading data for {experiment_id}:")

        # for each file in the experiment current folder either upload it to localstack
        # S3 or to dynamoDB
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
        logger.info("Going to populate mock S3/DynamoDB with experiment data.")
        populate_localstack()

    region = os.getenv("AWS_DEFAULT_REGION")
    logger.info("*" * 80)
    logger.info(f"InfraMock is RUNNING in mocked region {region}")
    logger.info("Check `docker-compose.yaml` for ports to acces services.")
    logger.info("Any other questions? Read the README, or ask on #engineering.")
    logger.info("*" * 80)


if __name__ == "__main__":
    main()
