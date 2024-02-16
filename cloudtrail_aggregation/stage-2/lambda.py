""" Lambda function to convert a month's worth of aggregated (NDJSON) CloudTrail logs
    into Parquet.

    The Lambda is triggered with a JSON payload that contains fields "month", and "year".
    """

import boto3
import gzip
import io
import json
import logging
import os

import pyarrow as pa
import pyarrow.parquet as pq

from datetime import datetime

SCHEMA = pa.schema([
    pa.field('event_id', pa.string()),
    pa.field('request_id', pa.string()),
    pa.field('shared_event_id', pa.string()),
    pa.field('event_time', pa.timestamp('ms')),
    pa.field('event_name', pa.string()),
    pa.field('event_source', pa.string()),
    pa.field('event_version', pa.string()),
    pa.field('aws_region', pa.string()),
    pa.field('source_ip_address', pa.string()),
    pa.field('recipient_account_id', pa.string()),
    pa.field('user_identity', pa.string()),
    pa.field('request_parameters', pa.string()),
    pa.field('response_elements', pa.string()),
    pa.field('additional_event_data', pa.string()),
    pa.field('resources', pa.string()),
])

NESTED_OBJECTS = {
    'userIdentity':         'user_identity',
    'requestParameters':    'request_parameters',
    'responseElements':     'response_elements',
    'additionalEventData':  'additional_event_data',
    'resources':            'resources'
}

s3_client = boto3.client('s3')

src_bucket = os.environ['SRC_BUCKET']
src_prefix = os.environ['SRC_PREFIX']
dst_bucket = os.environ['DST_BUCKET']
dst_prefix = os.environ['DST_PREFIX']
rows_per_file = int(os.environ['ROWS_PER_FILE'])

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", logging.INFO))


def lambda_handler(event, context):
    month, year = extract_trigger_message(event)
    logger.info(f"retrieving files for {year:04d}-{month:02d}")
    files = retrieve_file_list(month, year)
    logger.info(f"retrieved {len(files)} files")
    aggregate_and_output(files, month, year)


def extract_trigger_message(event):
    records = event['Records']
    if len(records) != 1:
        raise Exception(f"can only process 1 record at a time; received {len(records)}")
    message = json.loads(records[0]['body'])
    return message["month"], message["year"]


def retrieve_file_list(month, year):
    """ Retrieves the list of all files for the given year/month.
        """
    result = []
    req_args = {
        "Bucket": src_bucket,
        "Prefix": f"{src_prefix}{year:04d}/{month:02d}/"
    }
    while True:
        resp = s3_client.list_objects_v2(**req_args)
        for item in resp.get('Contents', []):
            result.append(item['Key'])
        if not resp.get('IsTruncated'):
            return result
        req_args['ContinuationToken'] = resp['NextContinuationToken']


def aggregate_and_output(file_list, month, year):
    """ Reads all of the input files, aggregates them into chunks based on the
        desired size, and writes them as parquet to the destination bucket and
        prefix.
        """
    file_number = 0
    cur_recs = []
    for rec in retrieve_log_records(file_list):
        cur_recs.append(rec)
        if len(cur_recs) >= rows_per_file:
            write_file(cur_recs, month, year, file_number)
            file_number += 1
            cur_recs = []
    if len(cur_recs) > 0:
        write_file(cur_recs, month, year, file_number)


def retrieve_log_records(file_list):
    """ A generator function that reads the aggregated log files, extracts the records,
        transforms them into a form that can be handled by PyArrow.
        """
    for file in file_list:
        for rec in read_file(file):
            yield transform_record(rec)


def read_file(key):
    """ Reads a source file from S3, uncompresses it, and returns the individual records.
        """
    logger.debug(f"reading s3://{src_bucket}/{key}")
    resp = s3_client.get_object(Bucket=src_bucket, Key=key)
    with resp['Body'] as body:
        data = body.read()
    if data.startswith(b'\x1f\x8b'):
        data = gzip.decompress(data)
    data = data.decode('utf-8')
    return [line for line in filter(lambda x: len(x) > 0, data.split('\n'))]


def transform_record(src_rec):
    """ Parses a single stringified JSON record, and reformats it to the form matching
        our output schema.
        """
    rec = json.loads(src_rec)
    xformed = {
        'event_id': rec.get('eventID'),
        'request_id': rec.get('requestID'),
        'shared_event_id': rec.get('sharedEventID'),
        'event_time': datetime.fromisoformat(rec.get('eventTime')),
        'event_name': rec.get('eventName'),
        'event_source': rec.get('eventSource'),
        'event_version': rec.get('eventVersion'),
        'aws_region': rec.get('awsRegion'),
        'source_ip_address': rec.get('sourceIPAddress'),
        'recipient_account_id': rec.get('recipientAccountId'),
    }
    for src_key, dst_key in NESTED_OBJECTS.items():
        if rec.get(src_key):
            xformed[dst_key] = json.dumps(rec.get(src_key))
        else:
            xformed[dst_key] = None
    return xformed


def write_file(records, month, year, file_number):
    """ Converts the passed records into a PyArrow table and writes them as a Parquet file.
        """
    s3_url = f"s3://{dst_bucket}/{dst_prefix}{year:04d}/{month:02d}/{file_number:06d}.parquet"
    logger.info(f"writing {len(records)} records to {s3_url}")
    table = pa.Table.from_pylist(records, schema=SCHEMA)
    pq.write_table(table, s3_url, compression='SNAPPY')
