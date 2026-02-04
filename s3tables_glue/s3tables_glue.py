import sys
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'AWS_ACCOUNT_ID', 'SOURCE_TABLE_BUCKET', 'SOURCE_NAMESPACE', 'SOURCE_TABLE', 'TARGET_TABLE', 'TARGET_S3_URL'])

catalog_id = f"{args['AWS_ACCOUNT_ID']}:s3tablescatalog/{args['SOURCE_TABLE_BUCKET']}"
warehouse = f"arn:aws:s3tables:us-east-1:{args['AWS_ACCOUNT_ID']}:bucket/{args['SOURCE_TABLE_BUCKET']}"

spark = SparkSession.builder.appName("SparkIcebergSQL") \
    .config("spark.jars.packages",                  "org.apache.iceberg:iceberg-spark-runtime-3.4_2.12:1.4.2") \
    .config("spark.sql.extensions",                 "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.example",            "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.example.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog") \
    .config("spark.sql.catalog.example.glue.id",    catalog_id) \
    .config("spark.sql.catalog.example.warehouse",  warehouse) \
    .getOrCreate()                                    

glueContext = GlueContext(spark.sparkContext)
job = Job(glueContext)
job.init("S3TablesExample", args)

selection = spark.sql(
    f"""
    SELECT  event_name, count(*) as event_count
    FROM    example.{args['SOURCE_NAMESPACE']}.{args['SOURCE_TABLE']}
    GROUP   BY event_name
    """)
                      
selection.createTempView("selection")

spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {args['TARGET_TABLE']}
    STORED AS PARQUET
    LOCATION '{args['TARGET_S3_URL']}'
    AS SELECT * from selection
    """)
    
job.commit()


