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

""" Credentials Lambda.

    This Lambda assumes a role that has permissions to upload a single file, and returns
    the credentials for that role session to the caller.
    """

import boto3
import json
import logging
import os

bucket = os.environ['UPLOAD_BUCKET']
role_arn = os.environ['ASSUMED_ROLE_ARN']

sts_client = boto3.client('sts')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) 

def lambda_handler(event, context):
    body = json.loads(event['body'])
    key = body['key']

    session_name = f"{context.function_name}-{context.aws_request_id}"
    session_policy = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Action': 's3:PutObject',
                'Resource': f"arn:aws:s3:::{bucket}/{key}"
            }
        ]
    }
    
    logger.info(f"generating restricted credentials for: s3://{bucket}/{key} for session {session_name}")
    
    response = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name,
        Policy=json.dumps(session_policy)
    )
    creds = response['Credentials']

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'access_key':     creds['AccessKeyId'],
            'secret_key':     creds['SecretAccessKey'],
            'session_token':  creds['SessionToken'],
            'region':         os.environ['AWS_REGION'],
            'bucket':         bucket
        })
    }
