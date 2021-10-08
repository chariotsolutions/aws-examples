import json
import os
import sys
import unittest

from unittest.mock import Mock


class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        os.environ['ES_HOSTNAME']           = "localhost:9200"
        os.environ['AWS_ACCESS_KEY_ID']     = "AKIADONTTHINKSO12345"
        os.environ['AWS_SECRET_ACCESS_KEY'] = "NONEOFYOURBUSINESS1234567891234455555555"
        os.environ['AWS_REGION']            = "us-east-1"

    def tearDown(self):
        if 'cloudtrail_to_elasticsearch.lambda_handler' in sys.modules:
            del sys.modules['cloudtrail_to_elasticsearch.lambda_handler']


    def test_import(self):
        """ This is a basic test to ensure that everything imports without problem. I
            use it as he first test for a Lambda handler, although later tests will
            generally do the same thing.
            """
        import cloudtrail_to_elasticsearch.lambda_handler


    def test_event_handling(self):
        """ Takes a sample S3 event (in this case, from the AWS docs) and verifies that
            it's deconstructed as passed to a mock handler.
            """
        import cloudtrail_to_elasticsearch.lambda_handler
        cloudtrail_to_elasticsearch.lambda_handler.px = mock = Mock()
        with open("tests/resources/s3_test_event.json") as f:
            event = json.load(f)
        cloudtrail_to_elasticsearch.lambda_handler.handle(event, None)
        mock.process_from_s3.assert_called_once_with("my-s3-bucket", "HappyFace.jpg")
