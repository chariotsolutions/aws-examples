#!/usr/bin/env python3
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

import boto3
import gzip


class S3Helper:
    """ Provides functions for interacting with S3. This class allows isolated unit
        testing of the operational modules.
    """

    def retrieve(self, bucket, key, gzipped=True):
        """ Retrieves the contents of an S3 object, optionally un-GZipping it.
        """
        object = boto3.resource('s3').Object(bucket, key)
        body = object.get()['Body']
        try:
            raw = body.read()
            if gzipped:
                return gzip.decompress(raw)
            else:
                return raw
        finally:
            body.close()


    def iterate_bucket(self, bucket, prefix, fn):
        """ Executes the provided function(bucket, key) for every key
            in the specified bucket with the specified prefix.
        """
        paginator = boto3.client('s3').get_paginator('list_objects')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page['Contents']:
                key = obj['Key']
                fn(bucket, key)

