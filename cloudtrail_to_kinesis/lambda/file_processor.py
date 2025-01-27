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
import logging
import time

from kinesis_writer import KinesisWriter 


logger = logging.getLogger(__name__)

class FileProcessor:

    FIELDS_TO_STRINGIFY = [
        "additionalEventData", "addendum", "edgeDeviceDetails", "insightDetails", 
        "requestParameters", "responseElements", "resources", "serviceEventDetails", 
        "tlsDetails", "userIdentity"
    ]


    def __init__(self, s3_client=None, kinesis_client=None):
        self.s3_client = s3_client
        self.kinesis_client = kinesis_client


    def extract_records(self, s3_bucket=None, s3_key=None, data=None):
        if not data:
            s3_result = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
            data = s3_result['Body'].read()
        if data.startswith(b'\x1f\x8b'):
             data = gzip.decompress(data)
        event = json.loads(data)
        records = event['Records']
        for rec in records:
            for field_name in FileProcessor.FIELDS_TO_STRINGIFY:
                field_value = rec.get(field_name)
                if field_value:
                    rec[field_name] = json.dumps(field_value)
        return records


    def process(self, s3_bucket=None, s3_key=None, data=None, stream_name=None):
        writer = KinesisWriter(self.kinesis_client, stream_name)
        recs = self.extract_records(s3_bucket=s3_bucket, s3_key=s3_key, data=data)
        for rec in recs:
            writer.enqueue(json.dumps(rec), rec.get('eventID'))    
        while writer.flush():
            time.sleep(0.25)
        logger.info(f"wrote {len(recs)} records")
