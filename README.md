# inframock

InfraMock is a local copy of the Biomage AWS stack for development purposes. It uses
[localstack](https://github.com/localstack/localstack) to create a mocked version of our AWS stack.
It can also, optionally, populate this stack with real data if local development is desired.

## How to use it

The following command will build and execute the inframock environment loading all the experiment data found in `BIOMAGE_DATA_PATH` folder:

    make build && make run

Use only `make run` if you don't want to rebuild the docker images.

If you want to reload the data you can run the following without having to stop inframock:

    make reload-data

This will only reload input data found in `BIOMAGE_DATA_PATH`. It will not erase generated files present in S3 like processed matrices, or plots. If you need a clean environment re-run inframock.

Run `make help` for more information about available commands like python linting and autoformatting.


You may want to use some additional environment variables. See the section down below for those.

## What's included

The following services are running within InfraMock:

* A Redis instance accessible from host port `6379`.
* An AWS-compatible endpoint accessible from host port `4566`.
* A PostgreSQL instance accessible from host post `5431`.

The endpoint on port `4566` is a drop-in replacement for the default AWS endpoint for a given
region. It has a working version of SQS, SNS, S3 running. Services are configured
to use the InfraMock-managed endpoint by default when run locally.

## Environment variables


The following environment variables are exposed for InfraMock:

`BIOMAGE_DATA_PATH`: where to get the experiment data to populate inframock's S3. It is recommended
to place it outside any other repositories to avoid interactions with git. For example, `export BIOMAGE_DATA_PATH=$HOME/biomage-data` (or next to where your biomage repos live). If this is not set, it will default to `./data`. **Note**: this should be permanently added to your environment (e.g. in `.zshrc`, `.localrc` or similar) because other services like `biomage-utils` or `worker` rely on using the same path.

`POPULATE_MOCK`: whether localstack should be filled with the data sets found in `BIOMAGE_DATA_PATH`.
For this to work, `CLUSTER_ENV` must be set to `development`, which is the default behavior.

`AWS_DEFAULT_REGION`: the default mocked region for your infrastructure to be deployed under. If it's not set,
it defaults to `eu-west-1`.

## Adding custom data


Inframock loads automatically the experiments found in the `BIOMAGE_DATA_PATH` folder. The default experiment included is the same found in the worker repo [here](https://github.com/biomage-org/worker/blob/master/data/test/r.rds.gz). The expected format for loading data is the following:


    /data
    |-- e52b39624588791a7889e39c617f669e
    |   |-- mock_experiment.json
    |   |-- mock_plots_tables.json
    |   |-- mock_samples.json
    |   `-- r.rds.gz


The naming convention for those files is:
 * Files for S3 must be named `r.rds.gz`
 * Files named in any other way will be ignored

You can add more data just add a new folder with the desired experiment ID and the 4 required files. If you need to reload your input data because you did
some changes you can just run `make reload-data` without having to stop inframock first.

**Notes**

* Manually adding data is not advised as it can lead to inconsistent states easily
* The recommendation is to use `biomage-utils` to download & synchronize experiments from staging or production (to be implemented soon)
* If you do add manually data, make sure the mock files and the r.rds.gz come from the same environment to avoid inconsistencies (i.e. copy both the rds & mock files from the same experiment in staging or production).

## Migrating SQL data

Knex is the Node.js package used to apply SQL migrations. The `knex` command configuration is done in the `api` repo. There are `make` commands available in `inframock` which references these `knex` commands. However, it assumes that the `api` folder is in the same level (i.e. contained in the same folder) as the `inframock` folder, so make sure that this is the case for your installation before continuing.

Before running the database migrations, make sure that knex is installed in the global context. To install knex, you can run `npm install knex -g`.

To apply the latest migrations in your local SQL instance:

1. `cd` to the root of `inframock`
2. Run `make migrate`.

If you would like to recreate (delete all data) your database:

1. `cd` to the root of `inframock`
2. Run `make cleanup-sql`
3. Restart `inframock`
3. Run `make migrate`

## FAQ

**Q: I want to directly access the AWS resources in InfraMock. How do I do this?**

A: The easiest way is to use the `aws-cli` along with InfraMock on a separate terminal.
You can add `--endpoint-url` as the *second* argument to
`aws`, which will automatically redirect all further requests to InfraMock. For example:

    $ aws --endpoint-url=http://localhost:4566 s3 ls s3://biomage-source-development-000000000000/5e959f9c9f4b120771249001/

will give you the following output:

    2021-01-06 18:05:43  149752480 python.h5ad
    2021-01-06 18:06:05   65803978 r.rds

where `biomage-source-development-000000000000` is the name of the s3 bucket that is created by inframock when starting the
local development infrastructure and `5e959f9c9f4b120771249001` is the experiment id that you are using locally.

Troubleshooting
---------------

**Pipeline error after restarting Inframock**
When restarting pipeline (`make run` from pipeline dir) after having started Inframock and Pipeline before, Inframock can throws this error below:

```
biomage-inframock-localstack | 2021-04-13T10:06:47:ERROR:cloudformation_api: Exception on / [POST]
biomage-inframock-localstack | Traceback (most recent call last):
biomage-inframock-localstack |   File
...
biomage-inframock-localstack |   File "/opt/code/localstack/localstack/utils/cloudformation/template_deployer.py", line 1759, in delete_stack
biomage-inframock-localstack |     self.stack.set_stack_status('DELETE_IN_PROGRESS')
```
This happens in situations when the previous run of Inframock hasn't been stopped successfully - the problem is that the old Cloudformation stack is being deleted as we are creating the new one. The way to fix this problem is to kill the containers that are running and then start Inframock again.


**Docker error after trying to kill currently running containers**

Docker throws this error when we try to kill currently running containers:

```
biomage-inframock-localstack | "docker kill" requires at least 1 argument(s).
biomage-inframock-localstack | See 'docker kill --help'.
biomage-inframock-localstack |
biomage-inframock-localstack | Usage:  docker kill [OPTIONS] CONTAINER [CONTAINER...]
```

That is an expected behavior, the idea is that it will try to kill an existing pipeline worker, but if it doesn't exist it doesn't throw. A similar thing happens in staging/production, Kubernetes will try to remove a Job that doesnt exist, return an error, that gets swallowed by the pipeline.

