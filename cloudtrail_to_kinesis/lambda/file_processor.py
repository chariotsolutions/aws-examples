import boto3
import gzip
import json
import time

from kinesis_writer import KinesisWriter 


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
        for rec in self.extract_records(s3_bucket=s3_bucket, s3_key=s3_key, data=data):
            writer.enqueue(json.dumps(rec), rec.get('eventID'))    
        while writer.flush():
            time.sleep(0.25)
