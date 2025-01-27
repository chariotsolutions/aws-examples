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

import base64
import boto3
import decimal
import json
import logging
import os
import uuid


logger = logging.getLogger(__name__)

table_name = os.environ['DYNAMO_TABLE_NAME']

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)


def handler(event, context):
    httpMethod = event['httpMethod']
    path = event['path']
    logger.info(f"invoked with method {httpMethod}, path {path}")
    id = extract_or_generate_id(httpMethod, event)
    logger.info(f"record ID: {id}")
    if httpMethod == "GET":
        return doGet(id)
    else:
        return doUpsert(id, event)


def extract_or_generate_id(httpMethod, event):
    if httpMethod == "POST":
        id = str(uuid.uuid4())
        logger.info(f"generated ID for POST: {id}")
        return id
    path_params = event['pathParameters']
    if path_params:
        id = path_params.get('id')
        if id:
            return id;
    raise Exception(f"unable to extract ID from path")


def doGet(id):
    item = table.get_item(Key={'id': id}, ConsistentRead=True).get('Item')
    if item:
        return success(item)
    else:
        return failure(404, "not found")


def doUpsert(id, event):
    body = event['body']
    if event.get('isBase64Encoded'):
        body = base64.b64decode(body).decode('utf-8')
    data = json.loads(body)
    data['id'] = id
    table.put_item(Item=data)
    return success(data)


def success(item):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(item, cls=MyJsonEncoder)
    }


def failure(status_code, reason):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "text/plain"
        },
        "body": reason
    }


class MyJsonEncoder(json.JSONEncoder):
    """ This class is a work-around for the DynamoDB "high-level" API returning
        values (set and Decimal) that aren't supported by the Python json module.
        """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            # we'll try to preserve integral values rather than coerce them to floating-point
            if o.as_tuple().exponent == 0:
                return int(o)
            else:
                return float(o)
        elif isinstance(o, set):
            return list(o)
        else:
            return super().default(o)
