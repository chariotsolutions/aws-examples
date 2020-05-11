################################################################################
# Copyright 2019 Chariot Solutions
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

""" Lambda function to upload CloudTrail events to Elasticsearch
"""

import processor

px = processor.create()

def lambda_handler(event, context):
    for record in event.get('Records', []):
        eventName = record['eventName']
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        try:
            print(f"processing s3://{bucket}/{key}")
            px.process_from_s3(bucket, key)
        except Exception as ex:
            print(f"failed to process file: {ex}")
