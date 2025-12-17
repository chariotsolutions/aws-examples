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

""" Tests for the firehose transform. 

    These use the default Python unit test framework to make builds simple (no
    need for a virtual environment or dependencies).
    """

import base64
import json
import os
import uuid
import unittest

import index


ENV_USE_SNAKE_CASE = "USE_SNAKE_CASE"
ENV_DISCARD_UNKNOWN_FIELDS = "DISCARD_UNKNOWN_FIELDS"
ENV_TRUNCATE_STRINGIFIED_FIELDS = "TRUNCATE_STRINGIFIED_FIELDS"


def default_cloudtrail_event():
    return json.loads("""
    {
        "eventVersion": "1.08",
        "userIdentity": {
            "type": "AWSService",
            "invokedBy": "resource-explorer-2.amazonaws.com"
        },
        "eventTime": "2025-12-09T16:31:31Z",
        "eventSource": "sts.amazonaws.com",
        "eventName": "AssumeRole",
        "awsRegion": "us-east-1",
        "sourceIPAddress": "resource-explorer-2.amazonaws.com",
        "userAgent": "resource-explorer-2.amazonaws.com",
        "requestParameters": {
            "roleArn": "arn:aws:iam::123456789012:role/aws-service-role/resource-explorer-2.amazonaws.com/AWSServiceRoleForResourceExplorer",
            "roleSessionName": "resource-explorer-2"
        },
        "responseElements": {
            "credentials": {
                "accessKeyId": "ASIA3ZHRCHV7JTRPPC7C",
                "sessionToken": "IQobJ3JZp2luX2VjPEn//////////REDACTED",
                "expiration": "Dec 9, 2025, 5:31:31 PM"
            },
            "assumedRoleUser": {
                "assumedRoleId": "AROA3ZHRHCV7FZIXJYFRM:resource-explorer-2",
                "arn": "arn:aws:sts::123456789012:assumed-role/AWSServiceRoleForResourceExplorer/resource-explorer-2"
            }
        },
        "additionalEventData": {
            "ExtendedRequestId": "MTp1cy1lYXN0LTE6UzoxNzY1Mjk3ODkxNTUwOlI6YnRZdllKM0s="
        },
        "requestID": "7a3135bc-f1f3-4034-b177-22c7ad08420c",
        "eventID": "44705871-5128-371c-a03f-f7247fba3713",
        "readOnly": true,
        "resources": [
            {
                "accountId": "123456789012",
                "type": "AWS::IAM::Role",
                "ARN": "arn:aws:iam::123456789012:role/aws-service-role/resource-explorer-2.amazonaws.com/AWSServiceRoleForResourceExplorer"
            }
        ],
        "eventType": "AwsApiCall",
        "managementEvent": true,
        "recipientAccountId": "123456789012",
        "sharedEventID": "541847a1-8e75-4c16-9df8-b371eda3f520",
        "eventCategory": "Management"
    }
    """)


def encode_message(msg):
    return base64.b64encode(json.dumps(msg).encode()).decode()


def decode_message(data):
    return json.loads(base64.b64decode(data.encode()).decode())


def construct_source(messages):
    result = []
    for msg in messages:
        result.append({
            "recordId": str(uuid.uuid4()),
            "data":     encode_message(msg)
        })
    return result


def setup_env(snake_case=None, discard_unknown=None, truncate_stringified=None):
    os.environ.pop(ENV_USE_SNAKE_CASE, None)
    os.environ.pop(ENV_DISCARD_UNKNOWN_FIELDS, None)
    os.environ.pop(ENV_TRUNCATE_STRINGIFIED_FIELDS, None)
    if snake_case:
        os.environ[ENV_USE_SNAKE_CASE] = snake_case
    if discard_unknown:
        os.environ[ENV_DISCARD_UNKNOWN_FIELDS] = discard_unknown
    if truncate_stringified:
        os.environ[ENV_TRUNCATE_STRINGIFIED_FIELDS] = truncate_stringified


class TestTransformationLambda(unittest.TestCase):

    def assert_record_ids(self, source_recs, result_recs):
        self.assertEqual(len(source_recs), len(result_recs), "different record counts")
        for ii in range(len(source_recs)):
            self.assertEqual(source_recs[ii]['recordId'], result_recs[ii]['recordId'], f"different record ID for rec {ii}")

    def assert_scalar_value(self, key, value):
        if value is not None:
            self.assertTrue(isinstance(value, (str,int,float,bool)), f"key {key} has non-supported value type: {type(value)}")


    def test_default_operation(self):
        setup_env()
        processor = index.Processor()
        source = construct_source([default_cloudtrail_event()])
        result = processor.process(source)
        self.assert_record_ids(source, result)
        source_rec = decode_message(source[0]['data'])
        result_rec = decode_message(result[0]['data'])
        self.assertEqual(len(source_rec.keys()), len(result_rec.keys()), "fields returned in result")
        self.assertEqual(source_rec.keys(), result_rec.keys(), "expected same keys in source and result")
        self.assertEqual(source_rec['eventID'], result_rec['eventID'], "spot check for non-converted key")
        for k,v in result_rec.items():
            self.assert_scalar_value(k, v)


    def test_use_snake_case(self):
        setup_env(snake_case="1")
        processor = index.Processor()
        source = construct_source([default_cloudtrail_event()])
        result = processor.process(source)
        self.assert_record_ids(source, result)
        source_rec = decode_message(source[0]['data'])
        result_rec = decode_message(result[0]['data'])
        self.assertEqual(len(source_rec.keys()), len(result_rec.keys()), "fields returned in result")
        self.assertNotEqual(source_rec.keys(), result_rec.keys(), "expected different keys in source and result")
        self.assertEqual(source_rec['eventID'], result_rec['event_id'], "spot check for converted key")
        for k,v in result_rec.items():
            self.assert_scalar_value(k, v)


    def test_discard_unknown_fields(self):
        setup_env(discard_unknown="1")
        processor = index.Processor()
        source = construct_source([{"eventID": "known", "argleBargle": "unknown"}])
        result = processor.process(source)
        result_rec = decode_message(result[0]['data'])
        self.assertEqual({"eventID": "known"}, result_rec)


    def test_retain_unknown_fields(self):
        setup_env(discard_unknown=None)
        processor = index.Processor()
        source = construct_source([{"eventID": "known", "argleBargle": "unknown"}])
        result = processor.process(source)
        result_rec = decode_message(result[0]['data'])
        self.assertEqual({"eventID": "known", "argleBargle": "unknown"}, result_rec)


    def test_retain_unknown_fields_and_convert_to_snake_case(self):
        setup_env(snake_case="1")
        processor = index.Processor()
        source = construct_source([{"eventID": "known", "argleBargle": "unknown"}])
        result = processor.process(source)
        result_rec = decode_message(result[0]['data'])
        self.assertEqual({"event_id": "known", "argle_bargle": "unknown"}, result_rec)


    def test_truncate_stringified_fields(self):
        setup_env(truncate_stringified="100")
        processor = index.Processor()
        source = construct_source([{"requestParameters": "x" * 200}])
        result = processor.process(source)
        result_rec = decode_message(result[0]['data'])
        self.assertEqual(100, len(result_rec["requestParameters"]), "length of stringified field (truncated)")


    def test_dont_truncate_stringified_fields(self):
        setup_env(truncate_stringified=None)
        processor = index.Processor()
        source = construct_source([{"requestParameters": "x" * 200}])
        result = processor.process(source)
        result_rec = decode_message(result[0]['data'])
        self.assertEqual(202, len(result_rec["requestParameters"]), "length of stringified field (including quotes)")


if __name__ == '__main__':
    unittest.main()
