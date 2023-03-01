#!/bin/env python3

""" Example X-Ray-enabled Glue job that measures the execution time of 
    PySpark DataFrame operations.
    """

import binascii
import boto3
import json
import pandas as pd
import os
import sys
import time
import uuid

from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import udf, pandas_udf
from pyspark.sql.types import StringType

from aws_xray_sdk.core import xray_recorder


##
## X-Ray related stuff
##

class CustomEmitter:
    """ This class replaces the default emitter in the X-Ray SDK, and writes
        directly to the X-Ray service rather than a daemon.
        """

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


xray_recorder.configure(
    emitter=CustomEmitter(),
    context_missing='LOG_ERROR',
    sampling=False)


##
## A UDF
##

def unique_ids(series: pd.Series) -> pd.Series:
    time.sleep(0.25)
    if series is not None:
        arr = [str(uuid.uuid4()) for value in series]
        row_count = len(arr)
        return pd.Series(arr)

unique_ids = pandas_udf(unique_ids, StringType()).asNondeterministic()


##
## The Glue job
##

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
job_name = args['JOB_NAME']

xray_recorder.begin_segment(job_name)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

with xray_recorder.in_subsegment("generate_dataframe"):
    df1 = spark.range(100000)

with xray_recorder.in_subsegment("add_unique_ids"):
    df2 = df1.withColumn('unique_id', unique_ids(df1.id))
    df2.foreach(lambda x : x) # forces evaluation of dataframe operation

with xray_recorder.in_subsegment("sort_dataframe"):
    df3 = df2.orderBy('unique_id')
    df3.foreach(lambda x : x)

df3.show()

xray_recorder.end_segment()

