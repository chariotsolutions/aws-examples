import json
import os
import sys
import unittest


# module under test
from cloudtrail_to_elasticsearch import processor


class TestTransforms(unittest.TestCase):

    def test_filename_to_index_name(self):
        filename = "123456789012/CloudTrail/us-east-1/2020/03/30/219289705433_CloudTrail_us-east-1_20200330T2110Z_T7Y7JlIYAD5Ej3HX.json.gz"
        expected_index_name = "cloudtrail-2020-03"
        self.assertEqual(expected_index_name, processor.index_name(filename), "index name extracted from filename")


    def test_bogus_filename_to_index_name(self):
        filename = "123456789012/CloudTrail/us-east-1/03/30/219289705433_CloudTrail_us-east-1_0330T2110Z_T7Y7JlIYAD5Ej3HX.json.gz"
        self.assertIsNone(processor.index_name(filename), "unparseable filename")


    def test_event_without_flattening(self):
        """ Removes the request_parameters and response_elements attributes from the source,
            since they don't have any values.
            """
        with open("tests/resources/simple_event.json") as f:
            orig = json.load(f)
        with open("tests/resources/simple_event-transformed.json") as f:
            expected = json.load(f)
        self.assertEqual(expected, processor.transform_events([orig])[0], "simple event, no flattening")


    def test_event_with_request_parameters(self):
        """ Replaces request_parameters with request_parameters_raw, a JSONified string representation,
            and request_parameters_flattened, a key->list representation.
            """
        with open("tests/resources/event_with_request_parameters.json") as f:
            orig = json.load(f)
        with open("tests/resources/event_with_request_parameters-transformed.json") as f:
            expected = json.load(f)
        self.assertEqual(expected, processor.transform_events([orig])[0], "simple event, no flattening")
