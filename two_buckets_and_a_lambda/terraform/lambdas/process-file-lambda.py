import boto3
import logging
import os
import urllib.parse

archive_bucket = os.environ['ARCHIVE_BUCKET']

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) 

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    for record in event.get('Records', []):
        eventName = record['eventName']
        bucket = record['s3']['bucket']['name']
        raw_key = record['s3']['object']['key']
        key = urllib.parse.unquote_plus(raw_key)
        try:
            logger.info(f"processing s3://{bucket}/{key}")
            process(bucket, key)
            logger.info(f"moving s3://{bucket}/{key} to s3://{archive_bucket}/{key}")
            archive(bucket, key)
        except Exception as ex:
            logger.exception(f"unhandled exception processing s3://{bucket}/{key}")


def process(bucket, key):
    meta = s3_client.head_object(Bucket=bucket, Key=key)
    logger.info(f"processing s3://{bucket}/{key} filesize = {meta['ContentLength']}")


def archive(bucket, key):
    s3_client.copy(
        CopySource={'Bucket': bucket, 'Key': key },
        Bucket=archive_bucket,
        Key=key)
    s3_client.delete_object(Bucket=bucket, Key=key)
