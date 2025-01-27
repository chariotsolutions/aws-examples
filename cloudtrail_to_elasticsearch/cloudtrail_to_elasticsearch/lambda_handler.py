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

""" Lambda function to upload CloudTrail events to Elasticsearch. This module
    decomposes the event and calls the processor module to do all the work.
    """


import json
import cloudtrail_to_elasticsearch.processor

px = cloudtrail_to_elasticsearch.processor.create()

def handle(event, context):
    for wrapper_record in event.get('Records', []):
        message = json.loads(wrapper_record['body'])
        for record in message.get('Records', []):
            eventName = record['eventName']
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            try:
                print(f"processing s3://{bucket}/{key}")
                px.process_from_s3(bucket, key)
            except Exception as ex:
                print(f"failed to process file: {ex}")
