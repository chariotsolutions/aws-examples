#!/bin/env python3

""" Example X-Ray-enabled Glue script that performs file conversions.

    This variant uses the AWS SDK (boto3) to record trace segments.
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


##
## This is the code to convert files from JSON into Avro; it has nothing to do
## with X-Ray (in this revision); jump ahead to the end of the file to see the
## relevant X-Ray code
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

arg_parser = argparse.ArgumentParser(description="Example of using AWS SDK calls")
arg_parser.add_argument("--data_bucket")
arg_parser.add_argument("--source_prefix", default="json")
arg_parser.add_argument("--dest_prefix", default="avro")
args = arg_parser.parse_known_args(sys.argv)[0]

job_name = "xray_glue-example_1"    # change this via parameter if you wish


##
## Setup for X-Ray: we create a unique trace ID and send the root segment
## to X-Ray (as an in-process segment it will be sent again at the end of
## the script).
##
## Note that I create the X-Ray client after getting the starting timestamp
## for the root segment: it can take a not-insignificant amount of time to
## create.
##

def rand_hex(num_bits):
    """ A helper function to create random IDs for X-Ray.
        """
    value = os.urandom(num_bits >> 3)
    return binascii.hexlify(value).decode()

xray_trace_id = "1-{:08x}-{}".format(int(time.time()), rand_hex(96))
xray_root_segment_id = rand_hex(64)
xray_root_segment = {
    "trace_id" : xray_trace_id,
    "id" : xray_root_segment_id,
    "name" : job_name,
    "start_time" : time.time(),
    "in_progress": True
}

xray_client = boto3.client('xray')
xray_client.put_trace_segments(TraceSegmentDocuments=[json.dumps(xray_root_segment)])


##
## The processing loop. For each file we'll create a new segment to capture the "process"
## function execution time. The actual script code is almost hidden by X-Ray-related code.
##

s3_bucket = boto3.resource('s3').Bucket(args.data_bucket)

for src in list(s3_bucket.objects.filter(Prefix=f"{args.source_prefix}/")):
    xray_start_timestamp = time.time()
    process(s3_bucket, src.key, args.dest_prefix)
    xray_child_segment = {
        "trace_id" : xray_trace_id,
        "id" : rand_hex(64),
        "parent_id": xray_root_segment_id,
        "name" : "process",
        "start_time" : xray_start_timestamp,
        "end_time": time.time()
    }
    xray_client.put_trace_segments(TraceSegmentDocuments=[json.dumps(xray_child_segment)])

##
## Lastly, we need to send an updated root segment that includes the end timestamp
##

del xray_root_segment["in_progress"]
xray_root_segment["end_time"] = time.time()
xray_client.put_trace_segments(TraceSegmentDocuments=[json.dumps(xray_root_segment)])
