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

""" Firehose Transformation Lambda for CloudTrail Events.

    This script accepts individual CloudTrail events and performs the following
    transformations:

    * Stringification of nested objects (always).
    * Transformation of top-level keys from camelCase to snake_case (controlled
      by the USE_SNAKE_CASE environment variable: 1 enables, 0 disables.
    * Removal of unknown top-level keys (controlled by the IGNORE_UNKNOWN_KEYS
      environment variable: 1 enables, 0 disables)

    """

import base64
import gzip
import json
import logging
import os
import re

from dataclasses import dataclass


ENV_USE_SNAKE_CASE = "USE_SNAKE_CASE"
ENV_DISCARD_UNKNOWN_FIELDS = "DISCARD_UNKNOWN_FIELDS"
ENV_TRUNCATE_STRINGIFIED_FIELDS = "TRUNCATE_STRINGIFIED_FIELDS"

CAMEL_CASE_MATCHER = re.compile(r'(?<=[a-z0-9])([A-Z]+)')


@dataclass
class FieldTransform:
    src_name: str
    dst_name: str
    stringify: bool = 0


FIELD_TRANSFORMS = [
    FieldTransform("eventID",               "event_id"),
    FieldTransform("eventTime",             "event_time"),
    FieldTransform("eventName",             "event_name"),
    FieldTransform("eventCategory",         "event_category"),
    FieldTransform("eventType",             "event_type"),
    FieldTransform("eventVersion",          "event_version"),
    FieldTransform("managementEvent",       "management_event"),
    FieldTransform("readOnly",              "read_only"),
    FieldTransform("awsRegion",             "aws_region"),
    FieldTransform("eventSource",           "event_source"),
    FieldTransform("apiVersion",            "api_version"),
    FieldTransform("recipientAccountId",    "recipient_account_id"),
    FieldTransform("sourceIPAddress",       "source_ip_address"),
    FieldTransform("requestID",             "request_id"),
    FieldTransform("sharedEventID",         "shared_event_id"),
    FieldTransform("requestParameters",     "request_parameters",       True),
    FieldTransform("responseElements",      "response_elements",        True),
    FieldTransform("resources",             "resources",                True),    
    FieldTransform("additionalEventData",   "additional_event_data",    True),
    FieldTransform("serviceEventDetails",   "service_event_details",    True),
    FieldTransform("userAgent",             "user_agent"),
    FieldTransform("userIdentity",          "user_identity",            True),
    FieldTransform("tlsDetails",            "tls_details",              True),
    FieldTransform("vpcEndpointId",         "vpc_endpoint_id"),
    FieldTransform("vpcEndpointAccountId",  "vpc_endpoint_account_id"),
    FieldTransform("errorCode",             "error_code"),
    FieldTransform("errorMessage",          "error_message"),
]

FIELD_TRANSFORMS_MAP = dict([(x.src_name, x) for x in FIELD_TRANSFORMS])


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Processor:

    def __init__(self):
        self._success_count = 0
        self._error_count = 0
        self._drop_count = 0
        # implementation note: we retrieve environment variables for each
        # instantiation to make testing easier
        self._use_snake_case = os.environ.get(ENV_USE_SNAKE_CASE, "0") == "1"
        self._discard_unknown_fields = os.environ.get(ENV_DISCARD_UNKNOWN_FIELDS, "0") == "1"
        self._truncate_stringified_fields = None
        if os.environ.get(ENV_TRUNCATE_STRINGIFIED_FIELDS):
            self._truncate_stringified_fields = int(os.environ.get(ENV_TRUNCATE_STRINGIFIED_FIELDS))


    def process(self, src_recs):
        logger.info(f"processing {len(src_recs)} records")
        result = [self._process_rec(rec) for rec in src_recs]
        logger.info(f"{self._success_count} successes, {self._error_count} errors, {self._drop_count} drops")
        return result


    def _process_rec(self, rec):
        record_id = rec['recordId']
        data = base64.b64decode(rec['data'])
        try:
            result = self._transform(data)
            if result:
                self._success_count += 1
                return {
                    'recordId': record_id,
                    'result': 'Ok',
                    'data': base64.b64encode(result).decode()
                }
            else:
                self._drop_count += 1
                return {
                    'recordId': record_id,
                    'result': 'Dropped'
                }
        except Exception as ex:
            logger.debug(f"unable to process record: {data}")
            self._error_count += 1
            return {
                'recordId': record_id,
                'result': 'ProcessingFailed',
                'data': base64.b64encode(data).decode()
            }


    def _transform(self, data):
        if data.startswith(b'\x1f\x8b'):
             data = gzip.decompress(data)
        parsed = json.loads(data.decode())
        result = {}
        for key in parsed.keys():
            val = parsed.get(key)
            xform = FIELD_TRANSFORMS_MAP.get(key)
            if xform:
                if self._use_snake_case:
                    key = xform.dst_name
                if xform.stringify:
                    val = json.dumps(val)
                    if self._truncate_stringified_fields:
                        val = val[:self._truncate_stringified_fields]
                result[key] = val
            elif not self._discard_unknown_fields:
                if self._use_snake_case:
                    key = CAMEL_CASE_MATCHER.sub(r'_\1', key).lower()
                if val is not None and not isinstance(val, (str,int,float,bool)):
                    val = json.dumps(val)
                    if self._truncate_stringified_fields:
                        val = val[:self._truncate_stringified_fields]
                result[key] = val
        reformatted = (json.dumps(result) + "\n")
        return reformatted.encode()


def lambda_handler(event, context):
    processor = Processor()
    return {"records": processor.process(event['records'])}
