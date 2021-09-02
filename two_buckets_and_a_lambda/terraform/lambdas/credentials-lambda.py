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

    session_name = f"{context.aws_request_id}"
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
    logger.info(f"role_arn is {role_arn}")
    
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
