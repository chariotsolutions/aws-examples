#!/bin/env python3

""" Example X-Ray-enabled Glue script that performs file conversions.

    This variant uses the X-Ray SDK to record trace segments, with a
    custom emitter to avoid the need for an X-Ray daemon.
    """

import argparse
import binascii
import boto3
import dateutil
import decimal
import fastavro
import io
import json
import os
import pathlib
import time
import sys

from datetime import datetime, timezone
from aws_xray_sdk.core import xray_recorder, patch


##
## This is the code to convert files from JSON into Avro. As written, it does
## not interact with X-Ray. However, you could update each of the methods with
## @xray_recorder.capture("segment_name") to trace the time spent in those
## functions.
##

def process(s3_bucket, src_key, dst_prefix):
    """ Downloads a single file, transforms it into Avro, and uploads it.
        """
    print(f"processing {src_key}")
    src_path = pathlib.PurePosixPath(src_key)
    file_type = src_path.parts[1]
    src_data = load_src_data(s3_bucket, src_key)
    dst_buf = io.BytesIO()
    if file_type == "addToCart" or file_type == "updateItemQuantity":
        handle_cart_events(src_data, dst_buf)
    elif file_type == "checkoutStarted" or file_type == "checkoutComplete":
        handle_checkout_events(src_data, dst_buf)
    else:
        raise Exception(f"unsupported file type: {file_type}")
    write_dst_data(s3_bucket, src_path, dst_prefix, dst_buf)


def load_src_data(s3_bucket, src_key):
    """ Reads the source file from S3 and returns an array of JSON objects.
        The source files are assumed to contain one or more NDJSON lines.
        """
    obj = s3_bucket.Object(src_key)
    buf = obj.get()['Body'].read()
    src = io.StringIO(buf.decode())
    return [json.loads(x) for x in src.readlines()]


def write_dst_data(s3_bucket, src_path, dst_prefix, buf):
    """ Writes the contents of the buffer into S3. Transforms the source
        path using the dstination prefix and ".avro" suffix.

        Note: we use the "avro/binary" content type, per description in
        https://avro.apache.org/docs/1.11.1/specification/#object-container-files
        but this type is not registered with IANA.
        """
    dst_path = pathlib.PurePosixPath(dst_prefix, *src_path.parts[1:]).with_suffix(".avro")
    dst_key = str(dst_path)
    obj = s3_bucket.Object(dst_key)
    obj.put(Body=buf, ContentType="avro/binary")


def handle_cart_events(src_data, dst_buf):
    def transform(rec):
        return {
            "eventType":    rec['eventType'],
            "eventId":      rec['eventId'],
            "timestamp":    dateutil.parser.parse(rec['timestamp']).replace(tzinfo=timezone.utc),
            "userId":       rec['userId'],
            "productId":    rec['productId'],
            "quantity":     int(rec['quantity']),
        }
    schema = fastavro.parse_schema({
                  "namespace": "com.chariotsolutions.example",
                  "type": "record",
                  "name": "AddToCart",
                  "fields": [
                    { "name": "eventType", "type": "string" },
                    { "name": "eventId", "type": "string" },
                    { "name": "timestamp", "type": { "type": "long", "logicalType": "timestamp-millis" } },
                    { "name": "userId", "type": "string" },
                    { "name": "productId", "type": "string" },
                    { "name": "quantity", "type": "int" },
                  ]
                })
    fastavro.writer(dst_buf, schema, [transform(rec) for rec in src_data])


def handle_checkout_events(src_data, dst_buf):
    def transform(rec):
        return {
            "eventType":    rec['eventType'],
            "eventId":      rec['eventId'],
            "timestamp":    dateutil.parser.parse(rec['timestamp']).replace(tzinfo=timezone.utc),
            "userId":       rec['userId'],
            "itemsInCart":  int(rec['itemsInCart']),
            "totalValue":   decimal.Decimal(rec['totalValue'])
        }
    schema = fastavro.parse_schema({
                  "namespace": "com.chariotsolutions.example",
                  "type": "record",
                  "name": "AddToCart",
                  "fields": [
                    { "name": "eventType", "type": "string" },
                    { "name": "eventId", "type": "string" },
                    { "name": "timestamp", "type": { "type": "long", "logicalType": "timestamp-millis" } },
                    { "name": "userId", "type": "string" },
                    { "name": "itemsInCart", "type": "int" },
                    { "name": "totalValue", "type": { "type": "bytes", "logicalType": "decimal", "precision": 16, "scale": 2 } }
                  ]
                })
    fastavro.writer(dst_buf, schema, [transform(rec) for rec in src_data])


##
## From here down is the "script" part of this job. It starts with us pulling out the
## invocation arguments that we care about (note that Glue adds a bunch of its own)
##

arg_parser = argparse.ArgumentParser(description="Example of using XRay SDK calls")
arg_parser.add_argument("--data_bucket")
arg_parser.add_argument("--source_prefix", default="json")
arg_parser.add_argument("--dest_prefix", default="avro")
args = arg_parser.parse_known_args(sys.argv)[0]

job_name = "xray_glue-example_2"    # change this via parameter if you wish


##
## This is the core part of this example: an emitter that writes directly to AWS,
## rather than to an X-Ray daemon
##

class DirectEmitter:

    def __init__(self):
        self.xray_client = None  # lazily initialize

    def send_entity(self, entity):
        if not self.xray_client:
            self.xray_client = boto3.client('xray')
        segment_doc = json.dumps(entity.to_dict())
        self.xray_client.put_trace_segments(TraceSegmentDocuments=[segment_doc])

    def set_daemon_address(self, address):
        pass

    @property
    def ip(self):
        return None

    @property
    def port(self):
        return None


##
## X-Ray configuration, including patching the Boto3 library.
##
## Note that we disable sampling: a Glue job is not executed so frequently
## that sampling becomes relevant, and unless we explicitly configure the
## recorder ## it will make an HTTP request to the daemon to retrieve the
## rules -- which ## will fail because the daemon isn't running
##

xray_recorder.configure(
    emitter=DirectEmitter(),
    context_missing='LOG_ERROR',
    sampling=False)

patch(['boto3'])


##
## The processing loop, with X-Ray context managers to establish the main segment
## and sub-segments.
##

with xray_recorder.in_segment(job_name):
    s3_bucket = boto3.resource('s3').Bucket(args.data_bucket)
    for src in list(s3_bucket.objects.filter(Prefix=f"{args.source_prefix}/")):
        with xray_recorder.in_subsegment("process"):
            process(s3_bucket, src.key, args.dest_prefix)

