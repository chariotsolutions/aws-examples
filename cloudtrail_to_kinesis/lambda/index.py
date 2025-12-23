################################################################################
#
# MIT No Attribution
#
# Copyright Chariot Solutions
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################

import boto3
import gzip
import json
import os
import time
import sys

from file_processor import FileProcessor
from kinesis_writer import KinesisWriter


# fail early if our one required envar isn't set
kinesis_stream = os.environ['KINESIS_STREAM']


def lambda_handler(event, context):
    kinesis_writer = KinesisWriter(boto3.client('kinesis'), kinesis_stream)
    fp = FileProcessor(boto3.client('s3'), kinesis_writer)
    for wrapper_record in event.get('Records', []):
        message = json.loads(wrapper_record['body'])
        for record in message.get('Records', []):
            eventName = record['eventName']
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            try:
                fp.process(s3_bucket=bucket, s3_key=key)
            except Exception as ex:
                print(f"failed to process file: {ex}")
    while kinesis_writer.flush():
        time.sleep(0.25)
