##
## Transforms JSON "clickstream data" into Parquet and Avro with specified schemas.
##

import sys

from awsglue.context import GlueContext, DynamicFrame
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions

from pyspark.context import SparkContext
from pyspark.sql import SparkSession, types

# schema definitions

PRODUCT_SCHEMA = types.StructType([
    types.StructField("eventId",      types.StringType(),  False),
    types.StructField("eventType",    types.StringType(),  False),
    types.StructField("timestamp",    types.TimestampType(),  False),
    types.StructField("userId",       types.StringType(),  False),
    types.StructField("productId",    types.StringType(),  True),
])

CART_SCHEMA = types.StructType([
    types.StructField("eventId",      types.StringType(),     False),
    types.StructField("eventType",    types.StringType(),     False),
    types.StructField("timestamp",    types.TimestampType(),  False),
    types.StructField("userId",       types.StringType(),     False),
    types.StructField("productId",    types.StringType(),     True),
    types.StructField("quantity",     types.IntegerType(),    True),
])

CHECKOUT_SCHEMA = types.StructType([
    types.StructField("eventId",      types.StringType(),  False),
    types.StructField("eventType",    types.StringType(),  False),
    types.StructField("timestamp",    types.TimestampType(),  False),
    types.StructField("userId",       types.StringType(),  False),
    types.StructField("itemsInCart",  types.IntegerType(), True),
    types.StructField("totalValue",   types.DecimalType(10,2),  True),
])

EVENTS_TO_SCHEMA = {
    "productPage":          PRODUCT_SCHEMA,
    "addToCart":            CART_SCHEMA,
    "checkoutStarted":      CHECKOUT_SCHEMA,
    "checkoutComplete":     CHECKOUT_SCHEMA,
    "updateItemQuantity":   CART_SCHEMA,
}

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET', 'AVRO_PREFIX', 'JSON_PREFIX', 'PARQUET_PREFIX'])

src_json = f"s3://{args['S3_BUCKET']}/{args['JSON_PREFIX']}"
dst_avro = f"s3://{args['S3_BUCKET']}/{args['AVRO_PREFIX']}"
dst_parquet = f"s3://{args['S3_BUCKET']}/{args['PARQUET_PREFIX']}"

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

for event_type, schema in EVENTS_TO_SCHEMA.items():
    df = spark.read.json(f"{src_json}/{event_type}/*.json", schema=schema, timestampFormat="yyyy-MM-dd HH:mm:ss.SSS")
    print(f"{event_type}: {df.count()}")
    dynf = DynamicFrame.fromDF(df, glueContext, event_type)
    # avro has issues with mixed-case fields, so convert everything to lowercase
    for field in schema.fields:
        dynf = dynf.rename_field(field.name, field.name.lower())
    avro_path = f"{dst_avro}/{event_type}/"
    glueContext.purge_s3_path(avro_path, options={"retentionPeriod": 0})
    glueContext.write_dynamic_frame.from_options(
        frame=dynf,
        connection_type="s3",
        connection_options={
            "path": avro_path
        },
        format="avro",
        format_options = {
            "version": "1.8"
        }
    )
    parquet_path = f"{dst_parquet}/{event_type}/"
    glueContext.purge_s3_path(parquet_path, options={"retentionPeriod": 0})
    glueContext.write_dynamic_frame.from_options(
        frame=dynf,
        connection_type="s3",
        connection_options={
            "path": parquet_path
        },
        format="parquet",
        format_options = {
        }
    )

job.commit()

