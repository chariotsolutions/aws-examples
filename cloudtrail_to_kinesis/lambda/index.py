import boto3
import gzip
import json
import os
import time
import sys

from file_processor import FileProcessor


kinesis_stream = os.environ['KINESIS_STREAM']
fp = FileProcessor(boto3.client('s3'), boto3.client('kinesis'))


def lambda_handler(event, context):
    for wrapper_record in event.get('Records', []):
        message = json.loads(wrapper_record['body'])
        for record in message.get('Records', []):
            eventName = record['eventName']
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            logger.info(f"processing s3://{bucket}/{key}")
            try:
                fp.process(s3_bucket=bucket, s3_key=key, stream_name=kinesis_stream)
            except Exception as ex:
                print(f"failed to process file: {ex}")
