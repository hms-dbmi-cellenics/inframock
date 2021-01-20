inframock
=========

InfraMock is a local copy of the Biomage AWS stack for development purposes. It uses localstack to
create a mocked version of our AWS stack. It can also, optionally, populate this stack with real data
if local development is desired.

How to use it
-------------

On MacOS, run

    docker-compose up --build

On Linux, run

    docker-compose -f docker-compose.linux-dev.yaml up --build

You may want to use some additional environment variables. See the section down below for those.

What's included
---------------
The following servies are running within InfraMock:

* A Redis instance accessible from host port `6379`.
* An AWS-compatible endpoint accessible from host port `4566`.
* A (pretty crappy) dashboard for said AWS-compatible endpoint running on port `8055`.

The endpoint on port `4566` is a drop-in replacement for the default AWS endpoint for a given
region. It has a working version of SQS, SNS, S3 and DynamoDB running. Services are configured
to use the InfraMock-managed endpoint by default when run locally.

Environment variables
---------------------

The following environment variables are exposed for InfraMock:

`POPULATE_MOCK`: whether localstack should be filled with a mocked PBMC data set. This is
set to `true` by default, which means that InfraMock will try to use a locally running version of 
the `api` to populate the localstack DynamoDB database with using its `/experiments/generate` endpoint. 
For this to work, `api` **must** be running with `CLUSTER_ENV` set to `development`, which is the default behavior.

`MOCK_EXPERIMENT_DATA_PATH`: where to get the mocked data for upload to the local S3 from. If
this is not set, it will default to the Github URL where the dataset used for the `worker` unit
test is located.

`AWS_DEFAULT_REGION`: the default mocked region for your infrastructure to be deployed under. If it's not set, 
it defaults to `eu-west-1`.

FAQ
---

**Q: I want to directly access the AWS resources in InfraMock. How do I do this?**

A: The easiest way is to use the `aws-cli` along with Inframock on a separate terminal.
You can add `--endpoint-url` as the *second* argument to
`aws`, which will automatically redirect all further requests to InfraMock. For example:

    $ aws --endpoint-url=http://localhost:4566 s3 ls s3://biomage-source

will give you the following output:

    2020-08-18 21:08:28   39909532 5e959f9c9f4b120771249001.h5ad

You can also use tools like [medis](https://github.com/luin/medis) for interactively debugging the local
Redis cache, and [NoSQL Workbench](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html)
to inspect and modify the current state of the local DynamoDB instance.
