""" A Lambda to initiate a CREATE TABLE AS operation on Athena and track its execution.

    There are two ways to invoke this Lambda:

        1)  Via SQS message from EventBridge Scheduler. This is the "normal" invocation,
            and the Lambda will use the message sent date to generate the CTAS query.
        2)  Via SQS message containing a JSON object that specifies the month and year
            to process. This is intended for manual execution and testing.
    """


import boto3
import json
import logging
import os
import time
import uuid

from datetime import datetime, timedelta, timezone


logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

athena_client = boto3.client('athena')
s3_client = boto3.client('s3')

athena_workgroup = os.environ['ATHENA_WORKGROUP']
glue_database = os.environ['GLUE_DATABASE']
src_table_name = os.environ['SRC_TABLE_NAME']
dst_table_name = os.environ['DST_TABLE_NAME']
dst_bucket_name = os.environ['DST_BUCKET']
dst_prefix = os.environ['DST_PREFIX']


def lambda_handler(event, context):
    month, year = extract_trigger_message(event)
    logger.info(f"processing {year:04d}-{month:02d}")
    logger.info("cleaning up from any previous run")
    drop_partition_table(month, year)
    delete_existing_files(month, year)
    logger.info("creating partition")
    create_partition_table(month, year)
    logger.info("removing temporary table")
    drop_partition_table(month, year)


def extract_trigger_message(event):
    records = event['Records']
    if len(records) != 1:
        raise Exception(f"can only process 1 record at a time; received {len(records)}")
    message = json.loads(records[0]['body'])
    if message.get('source') == "aws.scheduler":
        logger.info("invoked from EventBridge scheduler")
        dt = datetime.fromisoformat(message.get('time')) - timedelta(days=1)
        return dt.month, dt.year
    else:
        logger.info("invoked with explicit date")
        return message["month"], message["year"]


def drop_partition_table(month, year):
    execute_query(athena_client,
                  athena_workgroup,
                  f"DROP TABLE IF EXISTS {glue_database}.{partition_table_name(dst_table_name, month, year)};",
                  timeout=15)


def delete_existing_files(month, year):
    purge_s3_prefix(s3_client,
                    dst_bucket_name,
                    partition_table_prefix(dst_prefix, month, year))


def create_partition_table(month, year):
    execute_query(athena_client,
                  athena_workgroup,
                  f"""
                      CREATE TABLE {glue_database}.{partition_table_name(dst_table_name, month, year)}
                      WITH (
                              format = 'parquet',
                              bucketed_by = ARRAY['event_id'],
                              bucket_count = 4,
                              external_location = 's3://{dst_bucket_name}/{partition_table_prefix(dst_prefix, month, year)}',
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
                      from    {glue_database}.{src_table_name}
                      where   year = '{year:04d}'
                      and     month = '{month:02d}';
                      """.strip(),
                  timeout=60)


def partition_table_name(dst_table_name, month, year):
    return f"{dst_table_name}_temp_{year:04d}{month:02d}"


def partition_table_prefix(dst_table_prefix, month, year):
    # note: slash must already be part of prefix
    return f"{dst_table_prefix}{year:04d}/{month:02d}/"

##
## Below this point are some common utility functions
##

def execute_query(client, workgroup, query_text, request_token=None, timeout=None):
    """ Executes a query against Athena, returning execution ID.
        If timeout specified, will wait for query completion for that number of seconds, polling once per second.
        """
    resp = client.start_query_execution(
        QueryString=query_text,
        WorkGroup=workgroup,
        ClientRequestToken=request_token or str(uuid.uuid4()),
        ResultReuseConfiguration={'ResultReuseByAgeConfiguration': {'Enabled': False}}
    )
    query_execution_id = resp['QueryExecutionId']
    logger.debug(f"submitted query {query_execution_id}: {query_text[:16]}...")
    if timeout:
        waitfor_query(client, query_execution_id, timeout, throw_on_timeout=True)
    return query_execution_id


def waitfor_query(client, query_execution_id, timeout, throw_on_timeout=False, throw_on_cancelled=True):
    logger.debug(f"waiting up to {timeout} seconds for query {query_execution_id} completion")
    timeout_at = time.time() + timeout
    while time.time() < timeout_at:
        resp = client.get_query_execution(QueryExecutionId=query_execution_id)['QueryExecution']
        status = resp['Status']['State']
        if status == 'SUCCEEDED':
            return
        elif status == 'FAILED':
            message = resp['Status'].get('AthenaError', {}).get('ErrorMessage', "unknown error")
            raise Exception(f"query {query_execution_id} failed: {message}")
        elif status == 'CANCELLED':
            if throw_on_cancelled:
                raise Exception(f"query {query_execution_id} was cancelled")
            else:
                return
        # else status is QUEUED or RUNNING, so we wait
        time.sleep(1)
    if throw_on_timeout:
        raise Exception(f"timed-out waiting on query {query_execution_id}")


def purge_s3_prefix(client, bucket, prefix):
    logger.debug(f"purging files from s3://{bucket}/{prefix}")
    list_req = {
        'Bucket': bucket,
        'Prefix': prefix
    }
    while True:
        list_resp = client.list_objects_v2(**list_req)
        keys_to_delete = [obj['Key'] for obj in list_resp.get('Contents', [])]
        if keys_to_delete:
            logger.debug(f"deleting {len(keys_to_delete)} objects")
            del_resp = client.delete_objects(
                Bucket=bucket,
                Delete={'Objects': [{'Key': key} for key in keys_to_delete]}
            )
            del_list = del_resp.get('Deleted', [])
            err_list = del_resp.get('Errors', [])
            logger.debug(f"deleted {len(del_list)} objects; {len(err_list)} errors")
            if err_list:
                raise Exception(f"failed to delete {len(err_list)} records; sample: {err_list[0]}")
        else:
            logger.debug(f"no (more) objects to delete")
        if list_resp['IsTruncated']:
            list_req['ContinuationToken'] = list_resp['NextContinuationToken']
        else:
            return
