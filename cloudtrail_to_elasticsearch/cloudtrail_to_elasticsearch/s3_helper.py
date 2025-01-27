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

