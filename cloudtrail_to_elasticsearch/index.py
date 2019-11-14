""" Lambda function to upload CloudTrail events to Elasticsearch
"""

import boto3
import gzip
import json
import requests
import os

from aws_requests_auth.aws_auth import AWSRequestsAuth


s3 = boto3.resource('s3')

# AWS envars are provided by Lambda, ES_HOSTNAME by config
auth = AWSRequestsAuth(aws_access_key=os.environ['AWS_ACCESS_KEY_ID'],
                       aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
                       aws_token=os.environ['AWS_SESSION_TOKEN'],
                       aws_region=os.environ['AWS_REGION'],
                       aws_service='es',
                       aws_host=os.environ['ES_HOSTNAME'])


def lambda_handler(event, context):
    for record in event.get('Records', []):
        eventName = record['eventName']
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        indexName = 'cloudtrail-' + record['eventTime'][:10]
        if (eventName == 'ObjectCreated:Put') and (not 'CloudTrail-Digest' in key):
            process_file(bucket, key, indexName)


def process_file(bucket, key, indexName):
    print(f'processing s3://{bucket}/{key}')
    object = s3.Object(bucket, key)
    body = object.get()['Body']
    try:
        content = gzip.decompress(body.read())
        parsed = json.loads(content)
        upload(parsed.get('Records', []), indexName)
    finally:
        body.close()


def upload(events, indexName):
    print(f'writing {len(events)} events to index {indexName}')
    transformed = [transform(event, indexName) for event in events]
    rsp = requests.post('https://' + os.environ['ES_HOSTNAME'] + '/_bulk',
                        headers={'Content-Type': 'application/x-ndjson'},
                        auth=auth,
                        data="".join(transformed))
    if rsp.status_code != 200:
        print(f'unable to upload: {rsp.text}')


def transform(event, indexName):
    return "\n".join([
        json.dumps({ "index": { "_index": indexName, "_type": "cloudtrail-event", "_id": event['eventID'] }}),
        json.dumps(event)
        ]) + "\n"
