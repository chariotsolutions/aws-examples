""" Example Lambda using the Data API to update an Aurora Serverless table.
    """

import base64
import boto3
import json
import logging
import os
import sys
import uuid

from datetime import datetime, timezone

from functools import lru_cache


# fail fast if missing required configuration
secret_arn = os.environ["DB_SECRET_ARN"]
db_arn = os.environ["DB_INSTANCE_ARN"]

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", logging.INFO))


@lru_cache(maxsize=1)
def client():
    return boto3.client('rds-data')


def opt_out_user(email_address):
    logger.info(f"opt-out user: {email_address}")
    client().execute_statement(
        secretArn=secret_arn,
        resourceArn=db_arn,
        sql="""
            update EMAIL_PREFERENCES
            set    MARKETING_OPT_IN = false,
                   UPDATED_AT = :updated_at
            where  EMAIL_ADDRESS = :email_address
            """,
        parameters=[
            {                
                'name':     'email_address',
                'value':    {'stringValue': email_address}
            },
            {
                'name':     'updated_at',
                'typeHint': 'TIMESTAMP',
                'value':    {'stringValue': datetime.now().isoformat(sep=' ', timespec='seconds')}
            }
        ])


def process_record(rec):
    try:
        email_address = rec['email']
        notification_type = rec['event']
        logger.debug(f"{email_address}: {notification_type}")
        if notification_type in ['spamreport', 'unsubscribe']:
            opt_out_user(email_address)
    except:
        logger.warn("failed to process record", exc_info=True)


def lambda_handler(event, context):
    try:
        body = event['body']
        if event.get('isBase64Encoded'):
            body = str(base64.b64decode(body), 'utf-8')
        parsed = json.loads(body)
        logger.info(f"received {len(parsed)} records")
        for rec in parsed:
            process_record(rec)
    except:
        logger.warn("received an invalid event: body is missing, unparseable, or not an array of records")
    # returning 200 for all invocations because this is example code
    return {
        'statusCode': 200
    }
