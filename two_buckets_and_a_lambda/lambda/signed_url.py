""" Presigned URL Lambda

    This Lambda uses its own credentials to create a presigned URL that will allow
    the user to upload a file to S3.
    """

import boto3
import json
import logging
import os

bucket = os.environ['UPLOAD_BUCKET']

s3_client = boto3.client('s3')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) 

def lambda_handler(event, context):
    body = json.loads(event['body'])
    key = body['key']
    content_type = body['type']
    
    logger.info(f"generating presigned URL for: s3://{bucket}/{key} ({content_type})")
    
    params = {
        'Bucket':      bucket,
        'Key':         key,
        'ContentType': content_type
    }
    url = s3_client.generate_presigned_url('put_object', params)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'url': url
        })
    }
