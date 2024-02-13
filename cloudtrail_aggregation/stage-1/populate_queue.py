#!/usr/bin/env python3

import boto3
import json

from datetime import date, timedelta

QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/123456789012/cloudtrail-aggregation-trigger"

client = boto3.client('sqs')

dd = date(2023, 12, 1)
while dd <= date(2023, 12, 31):
    msg = json.dumps({"month": dd.month, "day": dd.day, "year": dd.year})
    client.send_message(QueueUrl=QUEUE_URL, MessageBody=msg)
    dd += timedelta(days=1)
