""" Lambda function to aggregate a single day's worth of CloudTriail log files.

    Files are read from a source bucket on S3, which is assumed to hold multiple
    accounts. The records from these files are then written to one or more files
    in the destination bucket, in NDJSON format and GZipped.

    The Lambda is triggered with a JSON payload that contains fields "month",
    "day", and "year".
    """

import boto3
import concurrent.futures
import gzip
import io
import json
import logging
import os

from datetime import datetime, timedelta, timezone


s3_client = boto3.client('s3')

src_bucket = os.environ['SRC_BUCKET']
src_prefix = os.environ['SRC_PREFIX']
dst_bucket = os.environ['DST_BUCKET']
dst_prefix = os.environ['DST_PREFIX']

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

threadpool = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def lambda_handler(event, context):
    month, day, year = extract_trigger_message(event)
    all_files = retrieve_file_list(month, day, year)
    aggregate_and_output(all_files, month, day, year)


def extract_trigger_message(event):
    records = event['Records']
    if len(records) != 1:
        raise Exception(f"can only process 1 record at a time; received {len(records)}")
    message = json.loads(records[0]['body'])
    if message.get('source') == "aws.scheduler":
        logger.info("invoked from EventBridge scheduler")
        dt = datetime.fromisoformat(message.get('time')) - timedelta(days=1)
        return dt.month, dt.day, dt.year
    else:
        logger.info("invoked with explicit date")
        return message["month"], message["day"], message["year"]


def retrieve_file_list(month, day, year):
    """ Retrieves the list of all files for the given date, for all accounts and regions.
        """
    logger.info(f"retrieving files for {year:04d}-{month:02d}-{day:02d}")
    all_files = []
    for account in retrieve_accounts():
        for region in retrieve_regions_for_account(account):
            files = retrieve_file_list_for_account_region_and_date(account, region, month, day, year)
            logger.debug(f"{len(files)} files for account {account}, region {region}")
            all_files += files
    logger.info(f"{len(all_files)} total files")
    return all_files


def retrieve_file_list_for_account_region_and_date(account_id, region, month, day, year):
    result = []
    prefix = f"{src_prefix}{account_id}/CloudTrail/{region}/{year:04d}/{month:02d}/{day:02d}/"
    logger.debug(f"listing files for prefix {prefix}")
    req_args = {
        "Bucket": src_bucket,
        "Prefix": prefix
    }
    while True:
        resp = s3_client.list_objects_v2(**req_args)
        for item in resp.get('Contents', []):
            result.append(item['Key'])
        if not resp.get('IsTruncated'):
            return result
        req_args['ContinuationToken'] = resp['NextContinuationToken']


def retrieve_accounts():
    return retrieve_child_prefixes(f"{src_prefix}")


def retrieve_regions_for_account(account_id):
    return retrieve_child_prefixes(f"{src_prefix}{account_id}/CloudTrail/")


def retrieve_child_prefixes(parent_prefix):
    """ Returns all child prefix components for a given parent prefix, sans trailing slashes.
        """
    logger.debug(f"retrieving child prefixes for {parent_prefix}")
    resp = s3_client.list_objects_v2(Bucket=src_bucket, Prefix=parent_prefix, Delimiter="/")
    result = []
    for prefix in [x['Prefix'] for x in resp.get('CommonPrefixes', [])]:
        trimmed = prefix.replace(parent_prefix, "").replace("/", "")
        result.append(trimmed)
    return result


def aggregate_and_output(file_list, month, day, year, desired_uncompressed_size = 64 * 1024 * 1024):
    """ Reads all of the input files, aggregates them into chunks based on the
        desired size (in reality, it's likely to be much smaller), and writes
        them to the destination bucket and prefix.
        """
    file_number = 0
    cur_recs = []
    cur_size = 0
    for rec in retrieve_log_records(file_list):
        cur_recs.append(rec)
        cur_size += len(rec)
        if cur_size >= desired_uncompressed_size:
            write_file(cur_recs, month, day, year, file_number)
            file_number += 1
            cur_recs = []
            cur_size = 0
    if len(cur_recs) > 0:
        write_file(cur_recs, month, day, year, file_number)


def retrieve_log_records(file_list):
    """ A generator function that reads CloudTrail log files, extracts the records,
        and the individual records from those files.
        """
    gathered = [parsed for parsed in threadpool.map(read_file, file_list)]
    for parsed in gathered:
        for rec in parsed['Records']:
            yield json.dumps(rec)


def read_file(key):
    """ Reads a source file from S3, uncompresses it if appropriate, and returns the contents.
        """
    logger.debug(f"reading s3://{src_bucket}/{key}")
    resp = s3_client.get_object(Bucket=src_bucket, Key=key)
    with resp['Body'] as body:
        data = body.read()
    if data.startswith(b'\x1f\x8b'):
        data = gzip.decompress(data)
    return json.loads(data)


def write_file(records, month, day, year, file_number):
    """ Writes records to a destination file, compressing them along the way.
        """
    out = io.StringIO()
    for rec in records:
        print(rec, file=out)
    data = out.getvalue().encode('utf-8')
    data = gzip.compress(data)
    key = f"{dst_prefix}{year:04d}/{month:02d}/{day:02d}/{file_number:06d}.ndjson.gz"
    logger.info(f"writing {len(records)} records to s3://{dst_bucket}/{key}")
    s3_client.put_object(Bucket=dst_bucket, Key=key, Body=data)
