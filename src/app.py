import boto3
import requests
import backoff
import logging
import sys
import simplejson as json
import gzip
import os
from pathlib import Path
from cfn_tools import load_yaml
from boto3.s3.transfer import TransferConfig

logger = logging.getLogger("inframock")
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
out_hdlr.setLevel(logging.DEBUG)
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)

populate_mock = os.getenv("POPULATE_MOCK")

datasets_location = os.getenv("MOCK_EXPERIMENT_DATA_PATH")
use_local_data = os.getenv("USE_LOCAL_DATA") == 'true'

MB = 1024 ** 2
config = TransferConfig(multipart_threshold=20*MB)

if use_local_data:
    datasets_location = os.getenv("LOCAL_DATA_PATH")


environment = "development"


@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_time=60)
def wait_for_localstack():
    logger.info(
        "Waiting for localstack to spin up..."
    )
    requests.get("http://localstack:4566")


def provision_biomage_stack():
    RESOURCES = ("dynamo", "s3", "sns")

    cf = boto3.resource("cloudformation", endpoint_url="http://localstack:4566")

    for resource in RESOURCES:
        path = f"https://raw.githubusercontent.com/biomage-ltd/iac/master/cf/{resource}.yaml"

        r = requests.get(path)
        stack_template = r.text

        stack = cf.create_stack(
            StackName=f"biomage-{resource}-development",
            TemplateBody=stack_template,
            Parameters=[
                {
                    "ParameterKey": "Environment",
                    "ParameterValue": "development",
                },
            ],
        )

    sns = boto3.client("sns", endpoint_url="http://localstack:4566")

    logger.warning(sns.list_topics())

    logger.info("Stack created.")
    return stack


def populate_mock_dynamo():

    FILES = [
        {
            'table': 'experiments',
            'filename': 'mock_experiment.json'
        },
        {
            'table': 'plots-tables',
            'filename': 'mock_plots_tables.json'
        }        
    ]

    experiment_data = None

    for f in FILES :
        with open(f['filename']) as json_file:
            data = json.load(json_file, use_decimal=True)

            dynamo = boto3.resource('dynamodb', endpoint_url="http://localstack:4566")
            table = dynamo.Table("{}-{}".format(f['table'], environment))

            if(data.get('records')) : 
                for data_item in data['records']:
                    table.put_item(
                        Item=data_item
                    )
            else:
                table.put_item(
                    Item=data
                )

            logger.info("Mocked {} loaded into local DynamoDB.".format(f['table']))

            if f['table'] == 'experiments':
                experiment_data = data
    
    return experiment_data

def find_biomage_source_bucket_name():
    return "biomage-source-development"


def populate_mock_s3(experiment_id):
    logger.debug(
        "Downloading data file to upload to mock S3 "
        f"for experiment id {experiment_id} ..."
    )

    FILES = [
        f"{datasets_location}/r.rds.gz"
    ]

    for f in FILES:

        if use_local_data:

            logger.debug(f"Using local data {f}")

            with open(f, mode='rb') as r:
                r.raw.decode_content = True
                contents = gzip.GzipFile(fileobj=r.raw, mode='rb')

                key = f"{experiment_id}/{Path(f).stem}"

                logger.debug(f"Found {f}, now uploading to S3 as {key} ...")
                s3 = boto3.resource("s3", endpoint_url="http://localstack:4566")

                s3.Object(find_biomage_source_bucket_name(),
                          f"{experiment_id}/{Path(f).stem}").upload_fileobj(Fileobj=contents, Config=config)

        else:

            logger.debug(f"Downloading {f}")

            with requests.get(f, allow_redirects=True, stream=True) as r:
                r.raw.decode_content = True
                contents = gzip.GzipFile(fileobj=r.raw, mode='rb')

                key = f"{experiment_id}/{Path(f).stem}"

                logger.debug(f"Downloaded {f}, now uploading to S3 as {key} ...")
                s3 = boto3.resource("s3", endpoint_url="http://localstack:4566")
                s3.Object(find_biomage_source_bucket_name(), f"{experiment_id}/{Path(f).stem}").put(Body=contents.read())

    logger.info("Mocked experiment data successfully uploaded to S3.")


def main():
    logger.info(
        "InfraMock local service started. Waiting for LocalStack to be brought up..."
    )
    wait_for_localstack()

    logger.info("LocalStack is up. Provisioning Biomage stack...")
    provision_biomage_stack()

    if populate_mock == "true":
        logger.info("Going to populate mock S3/DynamoDB with experiment data.")
        mock_experiment = populate_mock_dynamo()

        logger.info("Going to upload mocked experiment data to S3.")
        populate_mock_s3(experiment_id=mock_experiment["experimentId"])

    region = os.getenv("AWS_DEFAULT_REGION")
    logger.info("*" * 80)
    logger.info(f"InfraMock is RUNNING in mocked region {region}")
    logger.info("Check `docker-compose.yaml` for ports to acces services.")
    logger.info("Any other questions? Read the README, or ask on #engineering.")
    logger.info("*" * 80)


main()
