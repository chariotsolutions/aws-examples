""" An Airflow DAG that uses a CREATE TABLE AS (CTAS) query to aggregate one month
    of daily CloudTrail log files as a partition in a table. See README more details
    of this process.

    This DAG uses an AWS Connection to provide credentials, as well as region. The
    name of this connection is defined as a constant, as is the name of the bucket
    where data is stored. The month and year for aggregation is determined from the
    logical date of the DAG run.
    """

import json

from airflow.decorators import task
from airflow.models.dag import DAG

from airflow.providers.amazon.aws.hooks.athena import AthenaHook
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from airflow.providers.amazon.aws.sensors.athena import AthenaSensor
from airflow.providers.amazon.aws.operators.s3 import S3DeleteObjectsOperator


AWS_CONNECTION_ID = "aws_default"
BUCKET_NAME = "MY_BUCKET"
TABLE_NAME = "cloudtrail_athena"
SRC_TABLE_NAME = "cloudtrail_daily"


@task
def create_drop_query(logical_date):
    return """
        DROP TABLE IF EXISTS {base_table_name}_temp_{year}{month};
        """.format(
            base_table_name = TABLE_NAME,
            year = f"{logical_date.year:04}",
            month = f"{logical_date.month:02}")


@task
def create_ctas_query(logical_date):
    return """
        CREATE TABLE {base_table_name}_temp_{year}{month}
        WITH (
                format = 'parquet',
                bucketed_by = ARRAY['event_id'], 
                bucket_count = 4,
                external_location = 's3://{bucket_name}/{base_table_name}/{year}/{month}/',
                write_compression = 'SNAPPY'
        ) AS
        select  eventid                                                 as event_id,
                requestid                                               as request_id,
                cast(from_iso8601_timestamp(eventtime) as timestamp)    as event_time,
                eventsource                                             as event_source,
                eventname                                               as event_name,
                awsregion                                               as aws_region,
                sourceipaddress                                         as source_ip_address,
                recipientaccountid                                      as recipient_account_id,
                json_format(cast (useridentity as JSON))                as user_identity,
                useridentity.invokedby                                  as invoked_by,
                useridentity.principalid                                as principal_id,
                json_format(cast (resources as JSON))                   as resources
        from    {src_table_name}
        where   year = '{year}'
        and     month = '{month}';
        """.format(
            bucket_name = BUCKET_NAME,
            base_table_name = TABLE_NAME,
            src_table_name = SRC_TABLE_NAME,
            year = f"{logical_date.year:04}",
            month = f"{logical_date.month:02}")


with DAG("athena_ctas_dag",
         default_args={
            "aws_conn_id": AWS_CONNECTION_ID,
         },
        user_defined_macros={
            "bucket_name": BUCKET_NAME,
            "base_table_name": TABLE_NAME,
        }) as dag:

    create_drop_query = create_drop_query()

    submit_predrop = AthenaOperator(
        task_id="submit_predrop",
        database="default",
        query="{{ task_instance.xcom_pull(task_ids='create_drop_query') }}"
        )

    await_predrop = AthenaSensor(
        task_id="await_predrop",
        query_execution_id=submit_predrop.output,
    ) 

    delete_existing_data = S3DeleteObjectsOperator(
        task_id="delete_existing_data",
        bucket="{{ bucket_name }}",
        prefix='{{ base_table_name }}/{{ "{:04d}".format(logical_date.year) }}/{{"{:02d}".format(logical_date.month) }}/'
    )

    create_ctas_query = create_ctas_query()

    submit_ctas_query = AthenaOperator(
        task_id="submit_ctas_query",
        database="default",
        query="{{ task_instance.xcom_pull(task_ids='create_ctas_query') }}"
        )

    await_ctas_query = AthenaSensor(
        task_id="await_ctas_query",
        query_execution_id=submit_ctas_query.output,
    ) 

    submit_postdrop = AthenaOperator(
        task_id="submit_postdrop",
        database="default",
        query="{{ task_instance.xcom_pull(task_ids='create_drop_query') }}"
        )

    create_drop_query >> submit_predrop >> await_predrop >> delete_existing_data >> \
    create_ctas_query >> submit_ctas_query >> await_ctas_query >> \
    submit_postdrop
