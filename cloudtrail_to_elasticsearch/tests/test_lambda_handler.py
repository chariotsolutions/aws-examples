import os
import sys
import unittest


class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        os.environ['ES_HOSTNAME']           = "localhost:9200"
        os.environ['AWS_ACCESS_KEY_ID']     = "AKIADONTTHINKSO12345"
        os.environ['AWS_SECRET_ACCESS_KEY'] = "NONEOFYOURBUSINESS1234567891234455555555"
        os.environ['AWS_REGION']            = "us-east-1"


    # this test checks for any typing errors in import statements
    def test_import(self):
        import cloudtrail_to_elasticsearch.lambda_handler
