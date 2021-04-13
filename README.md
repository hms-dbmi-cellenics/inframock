inframock
=========

InfraMock is a local copy of the Biomage AWS stack for development purposes. It uses
[localstack](https://github.com/localstack/localstack) to create a mocked version of our AWS stack.
It can also, optionally, populate this stack with real data if local development is desired.

How to use it
-------------

The following command will build and execute the inframock environment loading all the experiment data found in `./data` folder:

    make run

If you want to reload the data you can run the following without having to stop inframock:

    make reload-data

This will only reload input data found in `./data`. It will not erase generated files present in S3 & DynamoDB like processed matrices, or plots. If you need a clean environment re-run inframock.

Run `make help` for more information about available commands like python linting and autoformatting.


You may want to use some additional environment variables. See the section down below for those.

What's included
---------------

The following services are running within InfraMock:

* A Redis instance accessible from host port `6379`.
* An AWS-compatible endpoint accessible from host port `4566`.

The endpoint on port `4566` is a drop-in replacement for the default AWS endpoint for a given
region. It has a working version of SQS, SNS, S3 and DynamoDB running. Services are configured
to use the InfraMock-managed endpoint by default when run locally.

Environment variables
---------------------

The following environment variables are exposed for InfraMock:

`BIOMAGE_DATA_PATH`: where to get the experiment data to populate inframock's S3 and DynamoDB. If
this is not set, it will default to `./data`.

`POPULATE_MOCK`: whether localstack should be filled with the data sets found in `BIOMAGE_DATA_PATH`.
For this to work, `CLUSTER_ENV` must be set to `development`, which is the default behavior.

`AWS_DEFAULT_REGION`: the default mocked region for your infrastructure to be deployed under. If it's not set,
it defaults to `eu-west-1`.

Adding custom data
---------------------

Inframock loads automatically the experiments found in the `./data` folder. The default experiment included is the same found in the worker repo [here](https://github.com/biomage-ltd/worker/blob/master/data/test/r.rds.gz). The expected format for loading data is the following:

/data
|-- e52b39624588791a7889e39c617f669e
|   |-- mock_experiment.json
|   |-- mock_plots_tables.json
|   |-- mock_samples.json
|   `-- r.rds.gz

The naming convention for those files is:
 * Files for DynamoDB must match:
     * `mock_plots_tables*.json`
     * `mock_samples*.json`
     * `mock_experiment*.json`
 * Files for S3 must be named `r.rds.gz`
 * Files named in any other way will be ignored

You can add more data just add a new folder with the desired experiment ID and the 4 required files. If you need to reload your input data because you did
some changes you can just run `make reload-data` without having to stop inframock first. 

**Notes**

* Manually adding data is not advised as it can lead to inconsistent states easily
* The recommendation is to use `biomage-utils` to download & synchronize experiments from staging or production (to be implemented soon) 
* If you do add manually data, make sure the mock files and the r.rds.gz come from the same environment to avoid inconsistencies (i.e. copy both the rds & mock files from the same experiment in staging or production).


FAQ
---

**Q: I want to directly access the AWS resources in InfraMock. How do I do this?**

A: The easiest way is to use the `aws-cli` along with InfraMock on a separate terminal.
You can add `--endpoint-url` as the *second* argument to
`aws`, which will automatically redirect all further requests to InfraMock. For example:

    $ aws --endpoint-url=http://localhost:4566 s3 ls s3://biomage-source-development/5e959f9c9f4b120771249001/

will give you the following output:

    2021-01-06 18:05:43  149752480 python.h5ad
    2021-01-06 18:06:05   65803978 r.rds

You can also use tools like [medis](https://github.com/luin/medis) for interactively debugging the local
Redis cache, and [NoSQL Workbench](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html)
to inspect and modify the current state of the local DynamoDB instance (`Operation Builder -> Add Connection`).
