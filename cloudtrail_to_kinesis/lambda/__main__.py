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

""" Entry point for processing a file locally.

    python . FILE_NAME KINESIS_STREAM

        FILE_NAME can be either an S3 URL or a local filename.
        KINESIS_STREAM is the name of a Kinesis Data Stream.

    To run, you must have boto3 available on your PYTHONPATH, and have all
    nevessary AWS permissions.
    """


import boto3
import logging
import re
import sys

from file_processor import FileProcessor

if len(sys.argv) != 3:
    print(__doc__)
    sys.exit(1)

logging.basicConfig(level=logging.INFO)

fp = FileProcessor(boto3.client('s3'), boto3.client('kinesis'))

m = re.match(r"s3:\/\/(.*?)\/(.*)", sys.argv[1])
if m:
    fp.process(s3_bucket=m.group(1), s3_key=m.group(2), stream_name=sys.argv[2])
else:
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
    fp.process(data=data, stream_name=sys.argv[2])
