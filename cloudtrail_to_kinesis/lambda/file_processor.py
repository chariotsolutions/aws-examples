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

""" Extracts records from a CloudTrail log file and writes them to the destination
    stream as stringified JSON. The file may live on either S3 or the local filesystem.

    A single instance can be called with multiple files, and will attempt to batch
    records from the file. Once all files have been processed, call flush() on the
    KinesisWriter.
    """

import boto3
import gzip
import json
import logging
import time


logger = logging.getLogger(__name__)


class FileProcessor:

    def __init__(self, s3_client=None, kinesis_writer=None):
        self._s3_client = s3_client
        self._kinesis_writer = kinesis_writer


    def process(self, s3_bucket=None, s3_key=None, file=None):
        recs = self._extract_records(s3_bucket=s3_bucket, s3_key=s3_key, file=file)
        for rec in recs:
            self._kinesis_writer.enqueue(json.dumps(rec), rec.get('eventID'))    
        logger.info(f"queued {len(recs)} records")


    def _extract_records(self, s3_bucket=None, s3_key=None, file=None):
        if not file:
            logger.info(f"reading from s3://{s3_bucket}/{s3_key}")
            s3_result = self._s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
            data = s3_result['Body'].read()
        else:
            logger.info(f"reading from {file}")
            with open(file, "rb") as f:
                data = f.read()
        if data.startswith(b'\x1f\x8b'):
             data = gzip.decompress(data)
        event = json.loads(data)
        return event['Records']
