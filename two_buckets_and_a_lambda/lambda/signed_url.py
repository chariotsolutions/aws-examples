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
